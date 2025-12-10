
import subprocess
import time
import logging
import requests
import re
import config
from anti_detection import AntiDetection
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamManager:
    def __init__(self):
        self.is_running = False
        self.process = None
        self.session_name = "fbstream"
        self.monitor_thread = None

    def parse_m3u8_for_best_quality(self, url):
        """اختيار أفضل جودة من M3U8"""
        try:
            headers = AntiDetection.obfuscate_stream_headers()
            resp = requests.get(url, headers=headers, timeout=10)
            
            if not resp.ok:
                logger.warning(f"⚠️ فشل تحميل M3U8: {resp.status_code}")
                return url
            
            content = resp.text
            qualities = []
            
            for line in content.split('\n'):
                if line.startswith('#EXT-X-STREAM-INF'):
                    match = re.search(r'BANDWIDTH=(\d+)', line)
                    if match:
                        bandwidth = int(match.group(1))
                        qualities.append((bandwidth, line))
            
            if qualities:
                qualities.sort(reverse=True)
                best_line = qualities[0][1]
                
                next_idx = content.split('\n').index(best_line) + 1
                lines = content.split('\n')
                if next_idx < len(lines):
                    best_url = lines[next_idx].strip()
                    if not best_url.startswith('http'):
                        base = url.rsplit('/', 1)[0]
                        best_url = f"{base}/{best_url}"
                    logger.info(f"✅ اختيار أفضل جودة: {qualities[0][0]} bps")
                    return best_url
            
            logger.info("📌 استخدام الرابط الأصلي")
            return url
            
        except Exception as e:
            logger.warning(f"⚠️ خطأ في تحليل M3U8: {e}")
            return url

    def get_tmux_session_exists(self):
        """التحقق من وجود جلسة tmux"""
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", self.session_name],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def kill_existing_session(self):
        """إيقاف الجلسة الموجودة"""
        try:
            if self.get_tmux_session_exists():
                subprocess.run(
                    ["tmux", "kill-session", "-t", self.session_name],
                    timeout=5
                )
                time.sleep(1)
                logger.info("🔄 تم إيقاف الجلسة القديمة")
        except Exception as e:
            logger.error(f"خطأ في إيقاف الجلسة: {e}")

    def start_stream(self, m3u8_url, stream_key):
        """بدء البث مع إعدادات محسّنة"""
        try:
            if self.is_running:
                return False, "⚠️ البث يعمل بالفعل!"
            
            self.kill_existing_session()
            
            rtmp_url = f"{config.FACEBOOK_RTMP_URL}{stream_key}"
            
            # أوامر FFmpeg محسّنة لفيسبوك
            cmd = [
                "ffmpeg",
                "-loglevel", "warning",
                "-stats",
                
                # إعدادات الإدخال - إعادة اتصال قوية
                "-reconnect", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "10",
                "-multiple_requests", "1",
                "-timeout", "10000000",
                "-rw_timeout", "10000000",
                
                # تحليل سريع
                "-analyzeduration", "3000000",
                "-probesize", "3000000",
                
                # User agent عشوائي
                "-user_agent", AntiDetection.get_random_user_agent(),
                
                # المصدر
                "-i", m3u8_url,
                
                # ترميز الفيديو - إعدادات مستقرة لفيسبوك
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-tune", "zerolatency",
                
                # معدل الإطارات ثابت (مهم جداً لفيسبوك)
                "-r", "30",
                "-g", "60",  # keyframe كل ثانيتين
                "-keyint_min", "60",
                "-sc_threshold", "0",  # تعطيل scene change detection
                
                # معدل البت
                "-b:v", "4500k",
                "-maxrate", "5000k",
                "-bufsize", "10000k",
                
                # البكسل
                "-pix_fmt", "yuv420p",
                "-profile:v", "high",
                "-level", "4.1",
                
                # الصوت
                "-c:a", "aac",
                "-b:a", "128k",
                "-ar", "44100",
                "-ac", "2",
                
                # مزامنة الصوت والفيديو
                "-async", "1",
                "-vsync", "cfr",  # constant framerate
                
                # إعدادات الإخراج لفيسبوك
                "-f", "flv",
                "-flvflags", "no_duration_filesize+no_metadata",
                "-strict", "experimental",
                
                rtmp_url
            ]
            
            # إضافة اللوجو إذا كان مفعلاً
            if config.LOGO_ENABLED:
                logo_filter = (
                    f"movie={config.LOGO_PATH}:loop=0,setpts=N/(FRAME_RATE*TB),"
                    f"scale={config.LOGO_SIZE},format=rgba,colorchannelmixer=aa={config.LOGO_OPACITY}"
                    f"[logo];[0:v][logo]overlay={config.LOGO_OFFSET_X}:{config.LOGO_OFFSET_Y}"
                )
                video_idx = cmd.index("-i") + 2
                cmd.insert(video_idx, "-vf")
                cmd.insert(video_idx + 1, logo_filter)
            
            # إنشاء أمر tmux
            ffmpeg_cmd = " ".join([f'"{arg}"' if " " in str(arg) else str(arg) for arg in cmd])
            tmux_cmd = [
                "tmux", "new-session", "-d", "-s", self.session_name,
                f"{ffmpeg_cmd} 2>&1 | tee /tmp/fbstream_$(date +%s).log"
            ]
            
            logger.info("🚀 بدء البث...")
            subprocess.run(tmux_cmd, timeout=10)
            
            # التحقق من الاتصال بعد 3 ثواني
            time.sleep(3)
            if not self.get_tmux_session_exists():
                return False, "❌ فشل بدء البث!\n\nتحقق من:\n- صحة الرابط\n- صحة Stream Key"
            
            # التحقق من الاستقرار بعد 10 ثواني
            time.sleep(7)
            if not self.get_tmux_session_exists():
                return False, "❌ البث توقف بعد البدء!\n\nالأسباب المحتملة:\n- Stream Key منتهي\n- مشكلة في المصدر"
            
            self.is_running = True
            self.process = True
            
            # بدء المراقبة
            self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
            self.monitor_thread.start()
            
            logger.info("✅ البث مستقر!")
            return True, "✅ البث يعمل!\n\n📺 افتح فيسبوك الآن\n⏱️ ستراه خلال ثوانٍ\n\n/stop لإيقاف البث"
            
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            self.process = None
            return False, f"❌ خطأ: {str(e)}"

    def stop_stream(self):
        """إيقاف البث"""
        try:
            if not self.is_running:
                return False, "⚠️ لا يوجد بث نشط."
            
            self.kill_existing_session()
            self.is_running = False
            self.process = None
            
            logger.info("⏹️ تم إيقاف البث")
            return True, "⏹️ تم إيقاف البث بنجاح!"
            
        except Exception as e:
            logger.error(f"خطأ في الإيقاف: {e}")
            return False, f"❌ خطأ في الإيقاف: {str(e)}"

    def get_detailed_status(self):
        """الحصول على حالة مفصلة"""
        if not self.is_running:
            return "⏸️ البث متوقف"
        
        if self.get_tmux_session_exists():
            return "✅ البث نشط ويعمل"
        else:
            self.is_running = False
            return "❌ البث توقف بشكل غير متوقع"

    def _monitor(self):
        """مراقبة البث"""
        check_interval = 5
        failures = 0
        
        while self.is_running:
            time.sleep(check_interval)
            
            if not self.get_tmux_session_exists():
                failures += 1
                logger.warning(f"⚠️ البث انقطع (محاولة {failures})")
                
                if failures >= 3:
                    logger.error("❌ البث فشل بشكل متكرر")
                    self.is_running = False
                    break
            else:
                failures = 0
                logger.info("✅ البث يعمل بشكل طبيعي")
