import subprocess
import logging
import config
import os
import time
import threading
import signal
import random
import requests
from urllib.parse import urljoin
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
        """بدء stunnel للاتصال الآمن بفيسبوك (قد لا يكون ضروري مع rtmps)"""
        logger.info("📌 استخدام RTMPS مباشرة بدون stunnel")
        return True

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

    def build_ffmpeg_command(self, m3u8_url, stream_key, logo_path=None, quality='high'):
        """بناء أمر FFmpeg مع تقنيات تجنب الكشف وتحسين الاتصال
        
        Args:
            m3u8_url: رابط البث (m3u8, ts, أو أي مصدر)
            stream_key: مفتاح البث في Facebook
            logo_path: مسار اللوجو (اختياري)
            quality: جودة البث - 'low' (low), 'medium' (medium), 'high' (default)
        """
        # استخدام RTMPS مباشرة - أكثر استقراراً وموثوقية
        rtmp_url = f"rtmps://live-api-s.facebook.com:443/rtmp/{stream_key}"
        
        # الحصول على معاملات عشوائية لتجنب الكشف
        anti_params = self.anti_detect.randomize_ffmpeg_params()
        
        # اكتشاف نوع المصدر
        is_ts_stream = '.ts' in m3u8_url or 'mpegts' in m3u8_url.lower() or ('?' in m3u8_url and 'm3u8' not in m3u8_url.lower())
        is_periscope = 'pscp.tv' in m3u8_url or 'periscope' in m3u8_url.lower()
        is_youtube = 'youtube' in m3u8_url.lower() or 'youtu' in m3u8_url.lower()
        is_twitch = 'twitch' in m3u8_url.lower() or 'twitch.tv' in m3u8_url.lower()
        
        # تحويل رابط الجودة المحددة إلى master playlist للاستقرار الأفضل
        if is_periscope and 'transcode/' in m3u8_url and 'dynamic_highlatency.m3u8' in m3u8_url:
            # تحويل من: .../transcode/.../dynamic_highlatency.m3u8
            # إلى: .../non_transcode/.../master_dynamic_highlatency.m3u8
            master_url = m3u8_url.replace('/transcode/', '/non_transcode/').replace('dynamic_highlatency.m3u8', 'master_dynamic_highlatency.m3u8')
            # إزالة المنفذ 443 لأنه غير ضروري في master
            master_url = master_url.replace(':443/', '/')
            logger.info(f"🔄 تحويل من جودة محددة إلى Master playlist للاستقرار")
            m3u8_url = master_url
        
        logger.info(f"📊 جودة البث المطلوبة: {quality.upper()}")
        logger.info(f"📡 المصدر: {'Periscope' if is_periscope else 'YouTube' if is_youtube else 'Twitch' if is_twitch else 'مصدر آخر'}")
        
        command = [
            config.FFMPEG_CMD,
            '-hide_banner',
            '-loglevel', 'info',
            '-nostats',
            # أولويات البروتوكول الآمنة
            '-protocol_whitelist', 'file,http,https,tcp,tls,crypto',
            '-tls_verify', '0',  # تجاوز مشاكل شهادات Twitter/Facebook
        ]
        
        # Reconnect parameters (تحسينات للاتصال الضعيف)
        if not is_ts_stream:
            command.extend([
                '-reconnect', '1',
                '-reconnect_streamed', '1', 
                '-reconnect_at_eof', '1',
                '-reconnect_delay_max', '20' if is_periscope else str(random.randint(5, 10)),
            ])
        
        # Timeouts محسّنة بناءً على نوع المصدر
        if is_periscope or is_twitch:
            timeout_val = '120000000'  # 120 ثانية للمصادر الضعيفة
            rw_timeout_val = '120000000'
        else:
            timeout_val = '60000000'
            rw_timeout_val = '60000000'
        
        command.extend([
            '-rw_timeout', rw_timeout_val,
            '-timeout', timeout_val,
            '-connect_timeout', '30000000',
            '-analyzeduration', '20000000' if is_periscope else '15000000',
            '-probesize', '50000000' if is_periscope else '30000000',
            '-fflags', '+genpts+igndts+discardcorrupt+nobuffer',
            '-err_detect', 'ignore_err',
            '-http_persistent', '1',
            '-user_agent', anti_params['user_agent'],
            '-headers', f'Referer: https://pscp.tv/\r\nConnection: keep-alive\r\n',
            
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
        
        # إعدادات الجودة بناءً على الطلب
        if quality.lower() == 'high':
            # جودة عالية - أفضل ممكن
            video_bitrate = '6000k'
            max_bitrate = '7000k'
            buffer_size = '14000k'
            audio_bitrate = '192k'
            preset = 'superfast'
            crf = '23'
        elif quality.lower() == 'medium':
            # جودة متوسطة - توازن
            video_bitrate = '4000k'
            max_bitrate = '4500k'
            buffer_size = '8000k'
            audio_bitrate = '128k'
            preset = 'ultrafast'
            crf = '26'
        else:  # low
            # جودة منخفضة - استقرار أفضل
            video_bitrate = '2500k'
            max_bitrate = '3000k'
            buffer_size = '5000k'
            audio_bitrate = '96k'
            preset = 'ultrafast'
            crf = '28'
        
        # تعديل الإعدادات للمصادر الضعيفة - أولوية الاستقرار على الجودة
        if is_periscope or is_twitch:
            preset = 'ultrafast'
            if quality.lower() == 'high':
                video_bitrate = '3500k'
                max_bitrate = '4000k'
                buffer_size = '7000k'
            else:
                video_bitrate = '2500k'
                max_bitrate = '3000k'
                buffer_size = '5000k'
        
        command.extend([
            '-c:v', 'libx264',
            '-preset', preset,
            '-tune', 'zerolatency',
            '-profile:v', 'baseline',  # استقرار أفضل مع الجميع
            '-level', '3.1',
            '-pix_fmt', 'yuv420p',
            
            '-r', '25',  # تقليل الـ frame rate للاستقرار
            '-fps_mode', 'passthrough',  # مرن أكثر من cfr
            '-g', '50',  # keyframe أقل تكراراً للاستقرار
            '-keyint_min', '20',
            '-sc_threshold', '0',
            '-nal-hrd', 'vbr',
            
            '-b:v', video_bitrate,
            '-maxrate', max_bitrate,
            '-bufsize', buffer_size,
            '-crf', '28',  # quality متوازنة
            
            '-c:a', 'aac',
            '-b:a', audio_bitrate,
            '-ar', '44100',  # معيار آمن
            '-ac', '2',
            
            '-movflags', '+faststart',
            '-fflags', '+genpts',
            '-max_muxing_queue_size', '4096',
            '-thread_queue_size', '512',
            
            # تجاوز مشاكل SSL/TLS مع Facebook RTMPS
            '-tls_verify', '0',
            '-f', 'flv',
            '-flvflags', 'no_duration_filesize+no_offset_filesize',
            
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

    def parse_m3u8_for_best_quality(self, m3u8_url):
        """تحليل M3U8 واختيار أعلى جودة متاحة تلقائياً"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://pscp.tv/',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(m3u8_url, headers=headers, timeout=30, verify=False)
            response.raise_for_status()
            m3u8_content = response.text
            
            # البحث عن URLs لتحديد الجودات
            bitrates = {}
            lines = m3u8_content.split('\n')
            
            for i, line in enumerate(lines):
                if 'EXT-X-STREAM-INF' in line:
                    # استخراج معدل البث
                    if 'BANDWIDTH=' in line:
                        bandwidth = int(line.split('BANDWIDTH=')[1].split(',')[0])
                        # الحصول على الرابط من السطر التالي
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line and not next_line.startswith('#'):
                                # تحويل الرابط النسبي إلى مطلق
                                if next_line.startswith('http'):
                                    quality_url = next_line
                                else:
                                    base_url = m3u8_url.rsplit('/', 1)[0]
                                    quality_url = urljoin(base_url + '/', next_line)
                                bitrates[bandwidth] = quality_url
            
            if bitrates:
                # اختيار أعلى معدل بث
                best_bandwidth = max(bitrates.keys())
                best_quality_url = bitrates[best_bandwidth]
                logger.info(f"🎬 تحليل M3U8: وجدنا {len(bitrates)} جودات متاحة")
                logger.info(f"✅ اختيار أفضل جودة: {best_bandwidth/1000:.0f}k")
                return best_quality_url
            
        except Exception as e:
            logger.warning(f"⚠️ لم نتمكن من تحليل M3U8: {e}")
        
        # إذا فشل التحليل، استخدم الرابط الأصلي
        return m3u8_url

    def start_stream(self, m3u8_url, rtmp_url, stream_key, logo_path=None, quality='high'):
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
        
        command = self.build_ffmpeg_command(m3u8_url, stream_key, logo_path, quality=quality)
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
