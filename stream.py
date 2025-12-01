import subprocess
import logging
import config
import os
import time
import threading
import signal
import random
from anti_detection import AntiDetection

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
        self.anti_detect = AntiDetection()

    def start_stunnel(self):
        """بدء stunnel للاتصال الآمن بفيسبوك"""
        try:
            self.stop_stunnel()
            
            config_content = """pid = /tmp/stunnel/stunnel.pid
foreground = yes
[fb-live]
client = yes
accept = 0.0.0.0:19350
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
                logger.info("✅ stunnel بدأ بنجاح على المنفذ 19350")
                return True
            else:
                stderr = self.stunnel_process.stderr.read().decode('utf-8', errors='ignore')
                logger.error(f"❌ stunnel فشل: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ في stunnel: {e}")
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
        """بناء أمر FFmpeg مع تقنيات تجنب الكشف وتحسين الاتصال"""
        rtmp_url = f"rtmp://127.0.0.1:19350/rtmp/{stream_key}"
        
        # الحصول على معاملات عشوائية لتجنب الكشف
        anti_params = self.anti_detect.randomize_ffmpeg_params()
        
        is_ts_stream = '.ts' in m3u8_url or 'mpegts' in m3u8_url.lower() or ('?' in m3u8_url and 'm3u8' not in m3u8_url.lower())
        is_periscope = 'pscp.tv' in m3u8_url or 'periscope' in m3u8_url.lower()
        
        # تحويل رابط الجودة المحددة إلى master playlist للاستقرار الأفضل
        if is_periscope and 'transcode/' in m3u8_url and 'dynamic_highlatency.m3u8' in m3u8_url:
            # تحويل من: .../transcode/.../dynamic_highlatency.m3u8
            # إلى: .../non_transcode/.../master_dynamic_highlatency.m3u8
            master_url = m3u8_url.replace('/transcode/', '/non_transcode/').replace('dynamic_highlatency.m3u8', 'master_dynamic_highlatency.m3u8')
            # إزالة المنفذ 443 لأنه غير ضروري في master
            master_url = master_url.replace(':443/', '/')
            logger.info(f"🔄 تحويل من جودة محددة إلى Master playlist للاستقرار")
            logger.info(f"📡 URL الأصلي: {m3u8_url[:80]}...")
            logger.info(f"📡 Master URL: {master_url[:80]}...")
            m3u8_url = master_url
        
        command = [
            config.FFMPEG_CMD,
            '-hide_banner',
            '-loglevel', 'warning',
        ]
        
        # Reconnect parameters (تحسينات للاتصال الضعيف)
        if not is_ts_stream:
            command.extend([
                '-reconnect', '1',
                '-reconnect_streamed', '1', 
                '-reconnect_at_eof', '1',
                '-reconnect_delay_max', '15' if is_periscope else str(random.randint(3, 8)),
            ])
        
        # Timeouts محسّنة للمصادر الضعيفة
        if is_periscope:
            timeout_val = '60000000'  # 60 ثانية للمصادر الضعيفة
            rw_timeout_val = '60000000'
        else:
            timeout_val = '30000000'
            rw_timeout_val = '30000000'
        
        command.extend([
            '-rw_timeout', rw_timeout_val,
            '-timeout', timeout_val,
            '-connect_timeout', '15000000',
            '-analyzeduration', '10000000' if is_periscope else '5000000',
            '-probesize', '20000000' if is_periscope else '10000000',
            '-fflags', '+genpts+igndts+discardcorrupt+nobuffer',
            '-err_detect', 'ignore_err',
            
            '-headers', f'User-Agent: {anti_params["user_agent"]}\r\nReferer: https://pscp.tv/\r\nConnection: keep-alive\r\n',
            
            '-i', m3u8_url,
        ])
        
        if logo_path and os.path.exists(logo_path):
            command.extend(['-i', logo_path])
            x_offset = int(str(config.LOGO_OFFSET_X).strip().strip('"').strip("'"))
            y_offset = int(str(config.LOGO_OFFSET_Y).strip().strip('"').strip("'"))
            logo_size = config.LOGO_SIZE
            
            overlay_pos = f"x=(W-w)+{x_offset}:y=(H-h)+({y_offset})"
            command.extend([
                '-filter_complex', f'[1:v]format=rgba,scale={logo_size}[logo];[0:v][logo]overlay={overlay_pos}[outv]',
                '-map', '[outv]',
                '-map', '0:a?',
            ])
        else:
            command.extend([
                '-map', '0:v:0',
                '-map', '0:a:0?',
            ])
        
        command.extend([
            '-c:v', 'libx264',
            '-preset', 'ultrafast' if is_periscope else anti_params['preset'],
            '-tune', 'zerolatency',
            '-profile:v', 'baseline',
            '-level', '3.1',
            '-pix_fmt', 'yuv420p',
            
            '-r', '30',
            '-fps_mode', 'cfr',
            '-vsync', 'cfr',
            
            '-b:v', anti_params['bitrate'],
            '-maxrate', str(int(anti_params['bitrate'].rstrip('k')) + 1000) + 'k' if is_periscope else str(int(anti_params['bitrate'].rstrip('k')) + 500) + 'k',
            '-bufsize', str(int(anti_params['bufsize'].rstrip('k')) * 2) + 'k' if is_periscope else anti_params['bufsize'],
            '-g', anti_params['gop'],
            '-keyint_min', '10' if is_periscope else '15',
            '-sc_threshold', '0',
            
            '-c:a', 'aac',
            '-b:a', '128k' if is_periscope else str(random.choice([96, 128])) + 'k',
            '-ar', '44100',
            '-ac', '2',
            
            '-max_muxing_queue_size', '1024' if is_periscope else '512',
            '-thread_queue_size', '256' if is_periscope else '128',
            '-f', 'flv',
            '-flvflags', 'no_duration_filesize',
            
            rtmp_url
        ])
        
        return command

    def monitor_process(self):
        """مراقبة العملية مع إعادة اتصال سريعة"""
        consecutive_failures = 0
        
        while self.is_running and self.process:
            if self.process.poll() is not None:
                self.reconnect_attempts += 1
                consecutive_failures += 1
                logger.warning(f"⚠️ البث توقف! محاولة {self.reconnect_attempts}/{self.max_reconnect_attempts}")
                
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    wait_time = min(2 * consecutive_failures, 10)
                    time.sleep(wait_time)
                    
                    if consecutive_failures >= 3:
                        logger.info("🔄 إعادة تشغيل stunnel...")
                        self.stop_stunnel()
                        time.sleep(1)
                        if not self.start_stunnel():
                            logger.error("❌ فشل إعادة تشغيل stunnel")
                            continue
                    
                    if self.is_running and self.last_command:
                        try:
                            self.process = subprocess.Popen(
                                self.last_command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                            )
                            logger.info("✅ تم إعادة الاتصال بنجاح")
                            time.sleep(5)
                            if self.process.poll() is None:
                                consecutive_failures = 0
                        except Exception as e:
                            logger.error(f"❌ فشل إعادة الاتصال: {e}")
                else:
                    logger.error("❌ تم الوصول للحد الأقصى من المحاولات")
                    self.is_running = False
                    self.stop_stunnel()
                    break
            else:
                if consecutive_failures > 0:
                    consecutive_failures = max(0, consecutive_failures - 1)
            time.sleep(3)

    def start_stream(self, m3u8_url, rtmp_url, stream_key, logo_path=None):
        """بدء البث مع تقنيات تجنب الكشف"""
        if self.process and self.process.poll() is None:
            return False, "⚠️ البث يعمل بالفعل! استخدم /stop أولاً."
        
        self.is_running = False
        self.process = None
        self.reconnect_attempts = 0
        
        logger.info("🔐 تفعيل حيل تجنب الكشف...")
        self.anti_detect.apply_stream_spacing()
        
        time.sleep(random.uniform(2, 5))
        
        logger.info("🚀 بدء stunnel...")
        if not self.start_stunnel():
            return False, "❌ فشل تشغيل الاتصال الآمن!\n\nحاول مرة أخرى."
        
        command = self.build_ffmpeg_command(m3u8_url, stream_key, logo_path)
        self.last_command = command
        
        logger.info(f"📺 بدء البث...")
        logger.info(f"📍 المصدر: {m3u8_url[:60]}...")
        
        try:
            log_file = open('/tmp/ffmpeg_output.log', 'w')
            self.process = subprocess.Popen(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT
            )
            
            logger.info(f"✅ FFmpeg بدأ بـ PID: {self.process.pid}")
            
            time.sleep(10)
            
            if self.process.poll() is not None:
                stderr = ""
                try:
                    with open('/tmp/ffmpeg_output.log', 'r') as f:
                        stderr = f.read()
                except:
                    pass
                
                logger.error(f"❌ FFmpeg فشل: {stderr[:500]}")
                self.process = None
                self.stop_stunnel()
                
                if "401" in stderr or "Unauthorized" in stderr:
                    return False, "❌ رابط M3U8 غير صالح أو انتهى!\n\nاحصل على رابط جديد."
                elif "403" in stderr:
                    return False, "❌ الوصول مرفوض من المصدر!"
                elif "Connection refused" in stderr or "refused" in stderr.lower():
                    return False, "❌ فشل الاتصال بفيسبوك!\n\nتأكد من:\n• Stream Key صحيح وجديد\n• صفحة Go Live مفتوحة في فيسبوك"
                elif "timed out" in stderr:
                    return False, "❌ انتهت مهلة الاتصال!"
                elif "Invalid argument" in stderr or "Unable to parse" in stderr:
                    return False, "❌ خطأ في معاملات البث! تحديث توقع."
                else:
                    return False, f"❌ فشل البث:\n{stderr[:200]}"
            
            self.is_running = True
            self.monitor_thread = threading.Thread(target=self.monitor_process, daemon=True)
            self.monitor_thread.start()
            
            return True, "✅ البث يعمل!\n\n🛡️ حيل التجنب مفعلة\n📺 افتح صفحة البث في فيسبوك.\n⏱️ انتظر 10-30 ثانية لظهور الفيديو.\n\nاستخدم /stop لإيقاف البث."
            
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
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
            return f"✅ البث نشط 🛡️\n📊 إعادة الاتصال: {status['reconnect_attempts']}/{self.max_reconnect_attempts}\n🔐 حيل التجنب: مفعلة"
        return "❌ البث متوقف"
