import subprocess
import time
import logging
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
        """استخدام الرابط مباشرة - FFmpeg سيتعامل معه"""
        logger.info("📌 استخدام الرابط مباشرة")
        return url.strip()

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
        """بناء أمر FFmpeg المحسّن لضمان 30fps و 3.5Mbps"""
        rtmp_url = f"{config.FACEBOOK_RTMP_URL}{stream_key}"
        user_agent = AntiDetection.get_random_user_agent()
        
        cmd = ["ffmpeg", "-y"]
        
        cmd.extend(["-loglevel", "warning", "-stats"])
        
        cmd.extend(["-fflags", "+genpts+discardcorrupt"])
        
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
            "-analyzeduration", "1000000",
            "-probesize", "1000000",
        ])
        
        cmd.extend(["-user_agent", user_agent])
        
        cmd.extend(["-i", m3u8_url])
        
        # تحقق من إمكانية استخدام اللوجو
        use_logo = config.LOGO_ENABLED and os.path.exists(config.LOGO_PATH)
        
        res_w = config.RESOLUTION_WIDTH
        res_h = config.RESOLUTION_HEIGHT
        
        if use_logo:
            try:
                cmd.extend(["-i", config.LOGO_PATH])
                
                ox = config.LOGO_OFFSET_X
                oy = config.LOGO_OFFSET_Y
                ox_str = f"W-w{abs(ox)}" if ox < 0 else str(ox)
                oy_str = f"H-h{abs(oy)}" if oy < 0 else str(oy)
                
                filter_complex = (
                    f"[0:v]scale={res_w}:{res_h},fps=30,format=yuv420p[base];"
                    f"[1:v]scale={config.LOGO_SIZE}:force_original_aspect_ratio=decrease,"
                    f"format=rgba,colorchannelmixer=aa={config.LOGO_OPACITY}[logo];"
                    f"[base][logo]overlay={ox_str}:{oy_str}:shortest=1:format=auto"
                )
                cmd.extend(["-filter_complex", filter_complex])
                logger.info(f"✅ اللوجو مفعّل - {res_h}p")
            except Exception as e:
                logger.warning(f"⚠️ تعذر إضافة اللوجو: {e}")
                use_logo = False
        
        if not use_logo:
            cmd.extend(["-vf", f"scale={res_w}:{res_h},fps=30,format=yuv420p"])
            logger.info(f"📺 البث بدون لوجو - {res_h}p")
        
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-threads", "1",
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
            "-minrate", "3000k",
            "-maxrate", "4000k",
            "-bufsize", "4000k",
        ])
        
        cmd.extend([
            "-pix_fmt", "yuv420p",
            "-profile:v", "main",
            "-level", "3.0",
        ])
        
        cmd.extend([
            "-c:a", "aac",
            "-b:a", "99k",
            "-ar", "48000",
            "-ac", "2",
        ])
        
        cmd.extend([
            "-f", "flv",
            "-flvflags", "no_duration_filesize",
            "-max_muxing_queue_size", "512",
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
            
            def escape_arg(arg):
                arg_str = str(arg)
                special_chars = [' ', '(', ')', '[', ']', ';', ':', '=', ',']
                if any(c in arg_str for c in special_chars):
                    escaped = arg_str.replace("'", "'\"'\"'")
                    return f"'{escaped}'"
                return arg_str
            
            ffmpeg_cmd_str = " ".join([escape_arg(arg) for arg in cmd])
            
            shell_cmd = f"{ffmpeg_cmd_str} 2>&1 | tee {self.log_file}"
            
            tmux_cmd = [
                "tmux", "new-session", "-d", "-s", self.session_name,
                "bash", "-c", shell_cmd
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
                logger.error(f"❌ البث فشل: {error_msg}")
                return False, f"❌ انقطع البث!\n\n{error_msg}\n\n💡 جرب:\n- تعطيل اللوجو في config.py\n- استخدام رابط M3U8 مختلف"
            
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
