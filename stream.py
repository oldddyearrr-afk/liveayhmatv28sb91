import subprocess
import logging
import config
import os
import time
import threading
import random
import requests
from urllib.parse import urljoin, urlparse
from anti_detection import AntiDetection

logger = logging.getLogger(__name__)

class StreamManager:
    def __init__(self):
        self.process = None
        self.is_running = False
        self.anti_detect = AntiDetection()
        self.monitor_thread = None
        self.current_source_type = None

    def detect_source_type(self, url):
        """اكتشاف نوع المصدر"""
        url_lower = url.lower()
        
        if 'pscp.tv' in url_lower or 'periscope' in url_lower:
            return 'periscope'
        if 'token=' in url_lower or url_lower.endswith('.ts'):
            return 'ts_direct'
        if any(x in url_lower for x in ['alkass', 'bein', 'ssc', 'shahid', 'mbc']):
            return 'sports'
        return 'hls'

    def build_ffmpeg_command(self, source_url, stream_key):
        """بناء أمر FFmpeg محسّن للاتصال المستقر"""
        rtmp_url = f"rtmps://live-api-s.facebook.com:443/rtmp/{stream_key}"
        source_type = self.detect_source_type(source_url)
        self.current_source_type = source_type
        
        logger.info(f"📡 النوع: {source_type}")
        
        # تحسين رابط Periscope
        if source_type == 'periscope' and 'transcode/' in source_url:
            source_url = source_url.replace('/transcode/', '/non_transcode/')
            source_url = source_url.replace('dynamic_highlatency.m3u8', 'master_dynamic_highlatency.m3u8')
            source_url = source_url.replace(':443/', '/')
        
        command = ['ffmpeg', '-hide_banner', '-loglevel', 'info', '-y']
        
        # إعدادات الإدخال المحسّنة
        command.extend([
            '-multiple_requests', '1',
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_at_eof', '1',
            '-reconnect_on_network_error', '1',
            '-reconnect_on_http_error', '4xx,5xx',
            '-reconnect_delay_max', '10',
            '-timeout', '10000000',
            '-rw_timeout', '10000000',
            '-analyzeduration', '5000000',
            '-probesize', '5000000',
            '-fflags', '+genpts+discardcorrupt+igndts',
            '-protocol_whitelist', 'file,http,https,tcp,tls,crypto,hls,httpproxy',
            '-user_agent', self.anti_detect.get_random_user_agent(),
            '-headers', 'Accept-Language: ar,en-US;q=0.9\r\nCache-Control: no-cache\r\n',
            '-i', source_url,
        ])
        
        # إعدادات الترميز المستقرة
        command.extend([
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-tune', 'zerolatency',
            '-profile:v', 'main',
            '-level', '4.1',
            '-pix_fmt', 'yuv420p',
            '-b:v', '3500k',
            '-maxrate', '4000k',
            '-bufsize', '7000k',
            '-g', '50',
            '-keyint_min', '25',
            '-sc_threshold', '0',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '44100',
            '-ac', '2',
            '-strict', '-2',
        ])
        
        # إعدادات الإخراج لـ Facebook
        command.extend([
            '-f', 'flv',
            '-flvflags', 'no_duration_filesize+no_metadata',
            '-flush_packets', '1',
            '-max_interleave_delta', '0',
            '-fflags', '+nobuffer+flush_packets',
            rtmp_url
        ])
        
        return command

    def start_stream(self, source_url, stream_key):
        """بدء البث"""
        if self.process and self.process.poll() is None:
            return False, "⚠️ البث يعمل بالفعل!"
        
        self.is_running = False
        self.process = None
        
        logger.info("🔐 جاري الاتصال...")
        time.sleep(random.uniform(1, 2))
        
        command = self.build_ffmpeg_command(source_url, stream_key)
        logger.info(f"📺 بدء البث...")
        
        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            logger.info(f"✅ FFmpeg بدأ (PID: {self.process.pid})")
            
            # انتظار 3 ثوانٍ للتحقق من الاتصال الأولي
            time.sleep(3)
            
            if self.process.poll() is not None:
                try:
                    stdout, _ = self.process.communicate(timeout=2)
                    logger.error(f"FFmpeg خرج مبكراً:\n{stdout}")
                except:
                    pass
                self.process = None
                return False, "❌ فشل الاتصال الأولي!\n\nتحقق من Stream Key والمصدر."
            
            # انتظار إضافي للتأكد من استقرار الاتصال
            logger.info("⏳ التحقق من استقرار الاتصال...")
            time.sleep(7)
            
            if self.process.poll() is not None:
                try:
                    stdout, _ = self.process.communicate(timeout=2)
                    logger.error(f"FFmpeg انقطع:\n{stdout}")
                except:
                    pass
                return False, "❌ الاتصال غير مستقر!\n\nقد يكون المصدر ضعيفاً أو Stream Key خاطئ."
            
            self.is_running = True
            self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
            self.monitor_thread.start()
            
            logger.info("✅ البث مستقر!")
            return True, "✅ البث يعمل ومستقر!\n\n📺 افتح فيسبوك الآن\n⏱️ ستراه خلال 10-15 ثانية\n\n💡 نصيحة: لا تغلق الصفحة حتى يظهر الفيديو\n\n/stop لإيقاف البث"
            
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            self.process = None
            return False, f"❌ خطأ: {str(e)}"

    def get_error_message(self, stderr):
        """ترجمة رسائل الخطأ"""
        if not stderr:
            return "❌ فشل البث!"
        
        s = stderr.lower()
        if "connection refused" in s:
            return "❌ Stream Key خطأ!\n\nتأكد من المفتاح صحيح."
        if "403" in stderr or "forbidden" in s:
            return "❌ الرابط محمي أو منتهي!"
        if "404" in stderr:
            return "❌ الرابط غير موجود!"
        if "timeout" in s:
            return "❌ انتهت المهلة!\n\nتحقق من الإنترنت."
        return "❌ فشل البث!\n\nتأكد من الرابط."

    def _monitor(self):
        """مراقبة البث مع محاولة إعادة الاتصال"""
        failures = 0
        while self.is_running and self.process:
            if self.process.poll() is not None:
                failures += 1
                logger.warning(f"⚠️ البث انقطع (محاولة {failures}/3)")
                
                if failures >= 3:
                    logger.error("❌ البث توقف نهائياً")
                    self.is_running = False
                    break
                
                # محاولة قراءة السبب
                try:
                    output = self.process.stdout.read() if self.process.stdout else ""
                    if output:
                        logger.error(f"آخر رسالة من FFmpeg: {output[-500:]}")
                except:
                    pass
                
                self.is_running = False
                break
            
            time.sleep(10)

    def stop_stream(self):
        """إيقاف البث"""
        self.is_running = False
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except:
                try:
                    self.process.kill()
                except:
                    pass
            self.process = None
        return True, "✅ تم إيقاف البث."

    def get_status(self):
        """حالة البث"""
        if self.process and self.process.poll() is None:
            return {'active': True}
        self.is_running = False
        return {'active': False}

    def get_detailed_status(self):
        """حالة مفصلة"""
        if self.get_status()['active']:
            return "✅ البث نشط"
        return "❌ البث متوقف"

    def parse_m3u8_for_best_quality(self, m3u8_url):
        """اختيار أفضل جودة من M3U8"""
        source_type = self.detect_source_type(m3u8_url)
        
        if source_type == 'ts_direct':
            return m3u8_url
        
        try:
            headers = {'User-Agent': self.anti_detect.get_random_user_agent()}
            response = requests.get(m3u8_url, headers=headers, timeout=10, verify=False)
            content = response.text
            
            if '#EXT-X-STREAM-INF' not in content:
                return m3u8_url
            
            bitrates = {}
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                if 'BANDWIDTH=' in line:
                    try:
                        bw = int(line.split('BANDWIDTH=')[1].split(',')[0])
                        next_line = lines[i + 1].strip()
                        if next_line and not next_line.startswith('#'):
                            if next_line.startswith('http'):
                                bitrates[bw] = next_line
                            else:
                                base = m3u8_url.rsplit('/', 1)[0]
                                bitrates[bw] = urljoin(base + '/', next_line)
                    except:
                        pass
            
            if bitrates:
                best = max(bitrates.keys())
                logger.info(f"🎬 اختيار أفضل جودة: {best/1000:.0f}k")
                return bitrates[best]
                
        except Exception as e:
            logger.warning(f"⚠️ {e}")
        
        return m3u8_url
