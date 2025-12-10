import subprocess
import time
import logging
import requests
import re
import os
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
        self.log_file = "/tmp/fbstream_latest.log"

    def parse_m3u8_for_best_quality(self, url):
        """اختيار أفضل جودة من M3U8"""
        try:
            headers = AntiDetection.obfuscate_stream_headers()
            headers['User-Agent'] = AntiDetection.get_random_user_agent()
            resp = requests.get(url, headers=headers, timeout=15)
            
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
                    capture_output=True,
                    timeout=5
                )
                time.sleep(1)
                logger.info("🔄 تم إيقاف الجلسة القديمة")
        except Exception as e:
            logger.error(f"خطأ في إيقاف الجلسة: {e}")

    def build_ffmpeg_command(self, m3u8_url, stream_key):
        """بناء أمر FFmpeg المحسّن"""
        rtmp_url = f"{config.FACEBOOK_RTMP_URL}{stream_key}"
        user_agent = AntiDetection.get_random_user_agent()
        
        cmd = ["ffmpeg", "-y"]
        
        cmd.extend(["-loglevel", "warning", "-stats"])
        
        cmd.append("-re")
        
        cmd.extend([
            "-reconnect", "1",
            "-reconnect_streamed", "1", 
            "-reconnect_delay_max", "5",
            "-reconnect_at_eof", "1",
        ])
        
        cmd.extend([
            "-timeout", "10000000",
            "-rw_timeout", "10000000",
            "-analyzeduration", "5000000",
            "-probesize", "5000000",
        ])
        
        cmd.extend(["-user_agent", user_agent])
        
        cmd.extend(["-i", m3u8_url])
        
        if config.LOGO_ENABLED and os.path.exists(config.LOGO_PATH):
            cmd.extend(["-i", config.LOGO_PATH])
            
            ox = config.LOGO_OFFSET_X
            oy = config.LOGO_OFFSET_Y
            
            if ox < 0:
                ox_str = f"W-w{ox}"
            else:
                ox_str = str(ox)
            
            if oy < 0:
                oy_str = f"H-h{oy}"
            else:
                oy_str = str(oy)
            
            filter_complex = (
                f"[1:v]scale={config.LOGO_SIZE},format=rgba,"
                f"colorchannelmixer=aa={config.LOGO_OPACITY}[logo];"
                f"[0:v][logo]overlay={ox_str}:{oy_str}:format=auto"
            )
            cmd.extend(["-filter_complex", filter_complex])
        
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-tune", "zerolatency",
        ])
        
        cmd.extend([
            "-r", "30",
            "-g", "60",
            "-keyint_min", "60",
            "-sc_threshold", "0",
            "-force_key_frames", "expr:gte(t,n_forced*2)",
        ])
        
        cmd.extend([
            "-b:v", "3500k",
            "-maxrate", "4000k",
            "-bufsize", "8000k",
        ])
        
        cmd.extend([
            "-pix_fmt", "yuv420p",
            "-profile:v", "high",
            "-level", "4.1",
        ])
        
        cmd.extend([
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-ac", "2",
        ])
        
        cmd.extend([
            "-f", "flv",
            "-flvflags", "no_duration_filesize",
            "-max_muxing_queue_size", "1024",
        ])
        
        cmd.append(rtmp_url)
        
        return cmd

    def start_stream(self, m3u8_url, stream_key):
        """بدء البث مع إعدادات محسّنة"""
        try:
            if self.is_running:
                return False, "⚠️ البث يعمل بالفعل!"
            
            self.kill_existing_session()
            
            if os.path.exists(self.log_file):
                os.remove(self.log_file)
            
            cmd = self.build_ffmpeg_command(m3u8_url, stream_key)
            
            ffmpeg_cmd_str = " ".join([
                f"'{arg}'" if " " in str(arg) or "(" in str(arg) or ")" in str(arg) else str(arg) 
                for arg in cmd
            ])
            
            shell_cmd = f"{ffmpeg_cmd_str} 2>&1 | tee {self.log_file}"
            
            tmux_cmd = [
                "tmux", "new-session", "-d", "-s", self.session_name,
                "bash", "-lc", shell_cmd
            ]
            
            logger.info("🚀 بدء البث...")
            logger.info(f"📝 الأمر: {' '.join(cmd[:15])}...")
            
            result = subprocess.run(
                tmux_cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                logger.error(f"❌ فشل tmux: {result.stderr}")
                return False, f"❌ فشل بدء الجلسة!"
            
            time.sleep(4)
            
            if not self.get_tmux_session_exists():
                error_msg = self._read_error_log()
                return False, f"❌ فشل البث!\n\n{error_msg}"
            
            time.sleep(6)
            
            if not self.get_tmux_session_exists():
                error_msg = self._read_error_log()
                return False, f"❌ انقطع البث!\n\n{error_msg}"
            
            self.is_running = True
            self.process = True
            
            self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
            self.monitor_thread.start()
            
            logger.info("✅ البث مستقر!")
            return True, "✅ البث يعمل!\n\n📺 افتح فيسبوك الآن\n⏱️ ستراه خلال ثوانٍ\n\n/stop لإيقاف البث"
            
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            self.process = None
            return False, f"❌ خطأ: {str(e)}"

    def _read_error_log(self):
        """قراءة لوج الأخطاء"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    content = f.read()
                    if content:
                        lines = content.strip().split('\n')
                        last_lines = lines[-5:] if len(lines) > 5 else lines
                        return "📋 " + "\n".join(last_lines)[:300]
            return "تحقق من الرابط و Stream Key"
        except:
            return "تحقق من الرابط و Stream Key"

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
        check_interval = 10
        failures = 0
        
        while self.is_running:
            time.sleep(check_interval)
            
            if not self.get_tmux_session_exists():
                failures += 1
                logger.warning(f"⚠️ البث انقطع (محاولة {failures})")
                
                if failures >= 2:
                    logger.error("❌ البث فشل")
                    self.is_running = False
                    break
            else:
                failures = 0
