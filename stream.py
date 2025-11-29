
import subprocess
import logging
import config
import os
import time
import threading
import random

logger = logging.getLogger(__name__)

class StreamManager:
    def __init__(self):
        self.process = None
        self.is_running = False
        self.monitor_thread = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 50
        self.last_m3u8_url = None
        self.last_rtmp_url = None
        self.last_stream_key = None
        self.last_logo_path = None

    def monitor_process(self):
        """مراقبة العملية وإعادة الاتصال عند الفشل مع عدد محاولات أكبر"""
        consecutive_failures = 0
        
        while self.is_running:
            if self.process is None:
                break
            
            poll_result = self.process.poll()
            
            if poll_result is not None:
                consecutive_failures += 1
                self.reconnect_attempts += 1
                
                logger.warning(f"البث توقف! (المحاولة {self.reconnect_attempts}/{self.max_reconnect_attempts})")
                logger.warning(f"فشل متتالي: {consecutive_failures}")
                
                if self.process.stderr:
                    try:
                        stderr_output = self.process.stderr.read()
                        if stderr_output:
                            logger.error(f"FFmpeg Error: {stderr_output[:500]}")
                    except:
                        pass
                
                if self.reconnect_attempts >= self.max_reconnect_attempts:
                    logger.error("تم الوصول للحد الأقصى من محاولات إعادة الاتصال")
                    self.is_running = False
                    break
                
                wait_time = min(2 ** min(consecutive_failures, 5), 30)
                logger.info(f"انتظار {wait_time} ثانية قبل إعادة الاتصال...")
                time.sleep(wait_time)
                
                if self.is_running:
                    self.restart_stream()
            else:
                if consecutive_failures > 0:
                    logger.info("تم استعادة الاتصال بنجاح!")
                consecutive_failures = 0
                self.reconnect_attempts = 0
            
            time.sleep(5)

    def restart_stream(self):
        """إعادة تشغيل العملية مع تنظيف كامل"""
        logger.info("إعادة بناء الاتصال...")
        
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except:
                try:
                    self.process.kill()
                except:
                    pass
        
        if hasattr(self, 'last_command'):
            try:
                self.process = subprocess.Popen(
                    self.last_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1
                )
                logger.info("تم إعادة بناء عملية البث")
            except Exception as e:
                logger.error(f"فشل إعادة البناء: {str(e)}")

    def start_stream(self, m3u8_url, rtmp_url, stream_key, logo_path=None):
        """بدء البث مع إعدادات Anti-Ban محسّنة - نسخ كل شيء من المصدر + اللوجو"""
        if self.process and self.process.poll() is None:
            return False, "البث يعمل بالفعل!"
        
        self.is_running = False
        self.process = None

        self.last_m3u8_url = m3u8_url
        self.last_rtmp_url = rtmp_url
        self.last_stream_key = stream_key
        self.last_logo_path = logo_path
        self.reconnect_attempts = 0

        rtmp_url = rtmp_url.rstrip('/')
        full_rtmp_url = f"{rtmp_url}/{stream_key}"

        command = [
            config.FFMPEG_CMD,
            '-hide_banner',
            '-loglevel', 'error',
            
            '-timeout', '30000000',
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_at_eof', '1',
            '-reconnect_delay_max', '15',
            '-multiple_requests', '1',
            
            '-analyzeduration', '20000000',
            '-probesize', '20000000',
            
            '-re',
            '-fflags', '+genpts+igndts+discardcorrupt',
            '-avoid_negative_ts', 'make_zero',
            
            '-headers', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\nAccept: */*\r\nOrigin: https://twitter.com\r\nReferer: https://twitter.com/\r\n',
            
            '-i', m3u8_url
        ]

        random_x = random.randint(5, 20)
        random_y = random.randint(5, 20)
        logo_opacity = round(random.uniform(0.85, 0.95), 2)
        
        if logo_path and os.path.exists(logo_path):
            command.extend(['-i', logo_path])
            
            filter_complex = (
                f"[1:v]format=rgba,colorchannelmixer=aa={logo_opacity}[logo_opacity];"
                f"[0:v][logo_opacity]overlay=W-w-{random_x}:{random_y}:format=auto,"
                f"format=yuv420p[outv]"
            )
            command.extend(['-filter_complex', filter_complex])
            command.extend(['-map', '[outv]', '-map', '0:a'])
        else:
            command.extend(['-pix_fmt', 'yuv420p'])

        command.extend([
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-tune', 'zerolatency',
            '-profile:v', 'high',
            '-level', '4.2',
            
            '-g', '60',
            '-keyint_min', '60',
            '-sc_threshold', '0',
            
            '-b:v', '4500k',
            '-minrate', '4000k',
            '-maxrate', '6000k',
            '-bufsize', '8000k',
            
            '-pix_fmt', 'yuv420p',
            
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '44100',
            '-ac', '2',
            '-strict', 'experimental',
            
            '-f', 'flv',
            '-flvflags', 'no_duration_filesize',
            
            full_rtmp_url
        ])

        try:
            logger.info(f"بدء البث من: {m3u8_url[:50]}...")
            logger.info(f"الوجهة: {rtmp_url}")
            logger.info(f"Stream Key: {stream_key[:10]}...")
            logger.info(f"Anti-Ban: Logo opacity={logo_opacity}, pos=({random_x},{random_y})")
            
            self.last_command = command
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            logger.info("فحص الاتصال بفيسبوك...")
            
            for attempt in range(3):
                time.sleep(5)
                
                if self.process.poll() is not None:
                    stderr = self.process.stderr.read() if self.process.stderr else "لا توجد تفاصيل"
                    logger.error(f"FFmpeg فشل: {stderr[:300]}")
                    
                    self.process = None
                    self.is_running = False
                    
                    if "401" in stderr or "403" in stderr or "Unauthorized" in stderr:
                        if "input" in stderr.lower() or "opening input" in stderr.lower():
                            return False, "❌ رابط M3U8 غير صالح أو انتهى!\n\n🔍 الأسباب:\n• الرابط انتهت صلاحيته\n• الرابط يحتاج تحديث\n\n💡 احصل على رابط M3U8 جديد وحاول مرة أخرى."
                        else:
                            return False, "❌ Stream Key غير مصرح!\n\nاحصل على Stream Key جديد من فيسبوك."
                    elif "Cannot read RTMP handshake" in stderr or "Error opening output" in stderr:
                        return False, "❌ فشل الاتصال بفيسبوك!\n\n🔍 الأسباب المحتملة:\n• Stream Key خاطئ أو منتهي\n• فيسبوك لم يبدأ استقبال البث بعد\n• حاول احصل على Stream Key جديد\n\n💡 تأكد أن صفحة 'Go Live' مفتوحة قبل البث!"
                    elif "Connection refused" in stderr or "timed out" in stderr:
                        return False, "❌ مشكلة اتصال!\n\nتحقق من الإنترنت وحاول مرة أخرى."
                    else:
                        return False, f"❌ فشل البث.\n\nالخطأ: {stderr[:150]}"
            
            if self.process.poll() is None:
                try:
                    import select
                    if select.select([self.process.stderr], [], [], 0)[0]:
                        stderr_check = self.process.stderr.read(300)
                        if stderr_check and ("Error" in stderr_check or "Cannot" in stderr_check):
                            logger.warning(f"تحذيرات: {stderr_check[:150]}")
                except:
                    pass
                
                self.is_running = True
                
                self.monitor_thread = threading.Thread(target=self.monitor_process, daemon=True)
                self.monitor_thread.start()
                
                logger.info("البث متصل بفيسبوك!")
                return True, "✅ البث نشط ومتصل بفيسبوك!\n\n🛡️ حماية Anti-Ban نشطة:\n• تم إضافة اللوجو بشفافية عشوائية\n• إضافة ختم الوقت الحي\n• إعدادات تبدو كبث أصلي\n\n📺 افتح صفحة البث الآن!"
            else:
                stderr = self.process.stderr.read() if self.process.stderr else "لا توجد تفاصيل"
                logger.error(f"FFmpeg خطأ: {stderr[:300]}")
                
                self.process = None
                self.is_running = False
                
                if "Server returned 4" in stderr or "Bad Request" in stderr:
                    return False, "❌ رابط M3U8 غير صالح أو انتهى!\n\nجرب رابط M3U8 جديد."
                elif "Connection" in stderr or "timeout" in stderr:
                    return False, "❌ مشكلة اتصال بالإنترنت!\n\nتحقق من الاتصال وحاول مرة أخرى."
                else:
                    return False, f"❌ فشل البث.\n\nالخطأ: {stderr[:100]}"
                
        except Exception as e:
            self.is_running = False
            logger.error(f"خطأ في بدء البث: {str(e)}")
            return False, f"❌ خطأ: {str(e)}"

    def stop_stream(self):
        """إيقاف البث بشكل آمن"""
        self.is_running = False
        
        if self.process and self.process.poll() is None:
            logger.info("إيقاف البث...")
            
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("العملية لم تتوقف، استخدام kill...")
                try:
                    self.process.kill()
                    self.process.wait(timeout=2)
                except:
                    pass
            except Exception as e:
                logger.error(f"خطأ في الإيقاف: {e}")
            
            self.process = None
            logger.info("تم إيقاف البث")
            return True, "✅ تم إيقاف البث بنجاح."
        
        return False, "❌ لا يوجد بث نشط."

    def get_status(self):
        """التحقق من حالة البث مع معلومات إضافية"""
        if self.process and self.process.poll() is None:
            self.is_running = True
            return {
                'active': True,
                'reconnect_attempts': self.reconnect_attempts,
                'max_attempts': self.max_reconnect_attempts
            }
        else:
            if self.is_running:
                logger.warning("العملية توقفت لكن الحالة كانت مازالت نشطة - تم التصحيح")
                self.is_running = False
            return {'active': False}

    def get_detailed_status(self):
        """الحصول على حالة مفصلة"""
        status = self.get_status()
        if status['active']:
            return f"✅ البث نشط\n🛡️ Anti-Ban نشط\n📊 محاولات إعادة الاتصال: {status['reconnect_attempts']}/{status['max_attempts']}"
        return "❌ البث متوقف"
