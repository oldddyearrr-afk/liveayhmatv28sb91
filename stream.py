import subprocess
import logging
import config
import os
import time
import threading
import signal

logger = logging.getLogger(__name__)

class StreamManager:
    def __init__(self):
        self.process = None
        self.stunnel_process = None
        self.is_running = False
        self.monitor_thread = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 50
        self.last_command = None

    def start_stunnel(self):
        """بدء stunnel للاتصال الآمن بفيسبوك"""
        try:
            self.stop_stunnel()
            
            config_content = """pid = /tmp/stunnel/stunnel.pid
foreground = yes
[fb-live]
client = yes
accept = 127.0.0.1:19350
connect = live-api-s.facebook.com:443
verifyChain = no
"""
            os.makedirs('/tmp/stunnel', exist_ok=True)
            with open('/tmp/stunnel/fb.conf', 'w') as f:
                f.write(config_content)
            
            self.stunnel_process = subprocess.Popen(
                ['stunnel', '/tmp/stunnel/fb.conf'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)
            
            if self.stunnel_process.poll() is None:
                logger.info("stunnel بدأ بنجاح على المنفذ 19350")
                return True
            else:
                stderr = self.stunnel_process.stderr.read().decode('utf-8', errors='ignore')
                logger.error(f"stunnel فشل: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في stunnel: {e}")
            return False

    def stop_stunnel(self):
        """إيقاف stunnel"""
        if self.stunnel_process:
            try:
                self.stunnel_process.terminate()
                self.stunnel_process.wait(timeout=3)
            except:
                try:
                    self.stunnel_process.kill()
                except:
                    pass
            self.stunnel_process = None
        
        try:
            subprocess.run(['pkill', '-f', 'stunnel'], capture_output=True, timeout=3)
        except:
            pass

    def build_ffmpeg_command(self, m3u8_url, stream_key, logo_path=None):
        """بناء أمر FFmpeg - يستخدم stunnel على المنفذ 19350"""
        rtmp_url = f"rtmp://127.0.0.1:19350/rtmp/{stream_key}"
        
        command = [
            config.FFMPEG_CMD,
            '-hide_banner',
            '-loglevel', 'warning',
            
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_at_eof', '1',
            '-reconnect_delay_max', '10',
            
            '-timeout', '30000000',
            '-analyzeduration', '10000000',
            '-probesize', '10000000',
            
            '-headers', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\nOrigin: https://twitter.com\r\nReferer: https://twitter.com/\r\n',
            
            '-i', m3u8_url,
        ]
        
        if logo_path and os.path.exists(logo_path):
            command.extend(['-i', logo_path])
            command.extend([
                '-filter_complex', '[1:v]format=rgba[logo];[0:v][logo]overlay=W-w-10:10[outv]',
                '-map', '[outv]',
                '-map', '0:a',
            ])
        
        command.extend([
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-tune', 'zerolatency',
            '-profile:v', 'high',
            '-level', '4.2',
            '-pix_fmt', 'yuv420p',
            
            '-b:v', '4500k',
            '-maxrate', '5000k',
            '-bufsize', '8000k',
            '-g', '60',
            
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '44100',
            '-ac', '2',
            
            '-f', 'flv',
            '-flvflags', 'no_duration_filesize',
            
            rtmp_url
        ])
        
        return command

    def monitor_process(self):
        """مراقبة العملية"""
        while self.is_running and self.process:
            if self.process.poll() is not None:
                logger.warning(f"البث توقف! (المحاولة {self.reconnect_attempts + 1}/{self.max_reconnect_attempts})")
                
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    self.reconnect_attempts += 1
                    time.sleep(5)
                    if self.is_running and self.last_command:
                        try:
                            self.process = subprocess.Popen(
                                self.last_command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                            )
                            logger.info("تم إعادة الاتصال")
                        except Exception as e:
                            logger.error(f"فشل إعادة الاتصال: {e}")
                else:
                    self.is_running = False
                    self.stop_stunnel()
                    break
            else:
                self.reconnect_attempts = 0
            time.sleep(5)

    def start_stream(self, m3u8_url, rtmp_url, stream_key, logo_path=None):
        """بدء البث"""
        if self.process and self.process.poll() is None:
            return False, "البث يعمل بالفعل! استخدم /stop أولاً."
        
        self.is_running = False
        self.process = None
        self.reconnect_attempts = 0
        
        logger.info("بدء stunnel...")
        if not self.start_stunnel():
            return False, "❌ فشل تشغيل الاتصال الآمن!\n\nحاول مرة أخرى."
        
        command = self.build_ffmpeg_command(m3u8_url, stream_key, logo_path)
        self.last_command = command
        
        logger.info(f"بدء البث...")
        logger.info(f"المصدر: {m3u8_url[:60]}...")
        logger.info(f"Stream Key: {stream_key[:15]}...")
        
        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            time.sleep(10)
            
            if self.process.poll() is not None:
                stderr = ""
                try:
                    stderr = self.process.stderr.read().decode('utf-8', errors='ignore')
                except:
                    pass
                
                logger.error(f"FFmpeg فشل: {stderr[:500]}")
                self.process = None
                self.stop_stunnel()
                
                if "401" in stderr or "Unauthorized" in stderr:
                    if "input" in stderr.lower():
                        return False, "❌ رابط M3U8 غير صالح أو انتهى!\n\nاحصل على رابط جديد."
                    return False, "❌ خطأ في المصادقة!"
                elif "403" in stderr:
                    return False, "❌ الوصول مرفوض! تحقق من الروابط."
                elif "Connection refused" in stderr:
                    return False, "❌ فشل الاتصال بفيسبوك!\n\nتأكد من:\n• Stream Key صحيح وجديد\n• صفحة Go Live مفتوحة في فيسبوك"
                elif "timed out" in stderr:
                    return False, "❌ انتهت مهلة الاتصال!\n\nتحقق من الإنترنت."
                else:
                    return False, f"❌ فشل البث:\n{stderr[:200]}"
            
            self.is_running = True
            self.monitor_thread = threading.Thread(target=self.monitor_process, daemon=True)
            self.monitor_thread.start()
            
            return True, "✅ البث يعمل!\n\n📺 افتح صفحة البث في فيسبوك.\n⏱️ انتظر 10-30 ثانية لظهور الفيديو.\n\nاستخدم /stop لإيقاف البث."
            
        except Exception as e:
            logger.error(f"خطأ: {e}")
            self.process = None
            self.stop_stunnel()
            return False, f"❌ خطأ: {str(e)}"

    def stop_stream(self):
        """إيقاف البث"""
        self.is_running = False
        
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                try:
                    self.process.kill()
                except:
                    pass
            self.process = None
        
        self.stop_stunnel()
        return True, "✅ تم إيقاف البث."

    def get_status(self):
        """حالة البث"""
        if self.process and self.process.poll() is None:
            return {'active': True, 'reconnect_attempts': self.reconnect_attempts}
        self.is_running = False
        return {'active': False}

    def get_detailed_status(self):
        """حالة مفصلة"""
        status = self.get_status()
        if status['active']:
            return f"✅ البث نشط\n📊 إعادة الاتصال: {status['reconnect_attempts']}/{self.max_reconnect_attempts}"
        return "❌ البث متوقف"
