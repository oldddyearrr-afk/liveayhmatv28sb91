import subprocess
import logging
import config
import os
import time
import threading
import random
import requests
from urllib.parse import urljoin, urlparse, parse_qs
from anti_detection import AntiDetection

logger = logging.getLogger(__name__)

class StreamManager:
    def __init__(self):
        self.process = None
        self.is_running = False
        self.anti_detect = AntiDetection()
        self.monitor_thread = None
        self.current_source_type = None
        self.reconnect_count = 0
        self.max_reconnects = 50

    def detect_source_type(self, url):
        """اكتشاف نوع المصدر بدقة"""
        url_lower = url.lower()
        parsed = urlparse(url)
        
        # Periscope / Twitter
        if 'pscp.tv' in url_lower or 'periscope' in url_lower:
            return 'periscope'
        
        # TS مباشر (روابط token مثل chervx)
        if 'token=' in url_lower or parsed.path.endswith('.ts'):
            return 'ts_direct'
        
        # قنوات رياضية (مثل alkass, beIN, etc)
        sports_domains = ['alkass', 'bein', 'ssc', 'shahid', 'mbc']
        if any(domain in url_lower for domain in sports_domains):
            return 'sports_channel'
        
        # HLS عادي
        if '.m3u8' in url_lower:
            return 'hls_standard'
        
        # MPEG-TS
        if 'mpegts' in url_lower or '/ts/' in url_lower:
            return 'mpegts'
        
        return 'unknown'

    def get_headers_for_source(self, source_type, url):
        """الحصول على Headers مناسبة حسب نوع المصدر"""
        base_headers = {
            'User-Agent': self.anti_detect.get_random_user_agent(),
            'Accept': '*/*',
            'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
        
        if source_type == 'periscope':
            base_headers.update({
                'Referer': 'https://twitter.com/',
                'Origin': 'https://twitter.com',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
            })
        elif source_type == 'sports_channel':
            parsed = urlparse(url)
            base_headers.update({
                'Referer': f'{parsed.scheme}://{parsed.netloc}/',
                'Origin': f'{parsed.scheme}://{parsed.netloc}',
            })
        elif source_type == 'ts_direct':
            parsed = urlparse(url)
            base_headers.update({
                'Referer': f'{parsed.scheme}://{parsed.netloc}/',
                'Accept-Encoding': 'identity',
            })
        
        return base_headers

    def build_ffmpeg_command(self, source_url, stream_key, logo_path=None, quality='ultra'):
        """بناء أمر FFmpeg محسّن لجميع أنواع المصادر"""
        rtmp_url = f"rtmps://live-api-s.facebook.com:443/rtmp/{stream_key}"
        
        # اكتشاف نوع المصدر
        source_type = self.detect_source_type(source_url)
        self.current_source_type = source_type
        
        logger.info(f"📡 نوع المصدر: {source_type}")
        logger.info(f"📊 الجودة: {quality.upper()}")
        
        # تحسين رابط Periscope
        if source_type == 'periscope':
            source_url = self.optimize_periscope_url(source_url)
        
        # الحصول على Headers
        headers = self.get_headers_for_source(source_type, source_url)
        
        command = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel', 'warning',
            '-y',
        ]
        
        # ═══════════════════════════════════════════════════════════
        # معاملات الإدخال حسب نوع المصدر
        # ═══════════════════════════════════════════════════════════
        
        if source_type == 'ts_direct':
            # TS مباشر - إعدادات خاصة
            command.extend([
                '-re',
                '-timeout', '10000000',
                '-rw_timeout', '10000000',
                '-reconnect', '1',
                '-reconnect_streamed', '1',
                '-reconnect_delay_max', '5',
                '-user_agent', headers['User-Agent'],
            ])
            if 'Referer' in headers:
                command.extend(['-referer', headers['Referer']])
            command.extend([
                '-i', source_url,
            ])
            
        elif source_type == 'periscope':
            # Periscope/Twitter - إعدادات محسّنة
            command.extend([
                '-multiple_requests', '1',
                '-reconnect', '1',
                '-reconnect_streamed', '1',
                '-reconnect_at_eof', '1',
                '-reconnect_on_network_error', '1',
                '-reconnect_on_http_error', '4xx,5xx',
                '-reconnect_delay_max', '3',
                '-analyzeduration', '5000000',
                '-probesize', '5000000',
                '-fflags', '+genpts+discardcorrupt+nobuffer+flush_packets',
                '-timeout', '10000000',
                '-rw_timeout', '10000000',
                '-protocol_whitelist', 'file,http,https,tcp,tls,crypto,hls',
                '-tls_verify', '0',
                '-user_agent', headers['User-Agent'],
                '-headers', f"Referer: {headers.get('Referer', 'https://twitter.com/')}\r\nOrigin: {headers.get('Origin', 'https://twitter.com')}\r\n",
                '-i', source_url,
            ])
            
        elif source_type == 'sports_channel':
            # قنوات رياضية - إعدادات استقرار عالي
            command.extend([
                '-multiple_requests', '1',
                '-reconnect', '1',
                '-reconnect_streamed', '1',
                '-reconnect_at_eof', '1',
                '-reconnect_on_network_error', '1',
                '-reconnect_on_http_error', '4xx,5xx',
                '-reconnect_delay_max', '2',
                '-analyzeduration', '3000000',
                '-probesize', '3000000',
                '-fflags', '+genpts+discardcorrupt+nobuffer+flush_packets+igndts',
                '-timeout', '8000000',
                '-rw_timeout', '8000000',
                '-protocol_whitelist', 'file,http,https,tcp,tls,crypto,hls',
                '-tls_verify', '0',
                '-user_agent', headers['User-Agent'],
            ])
            if 'Referer' in headers:
                command.extend(['-referer', headers['Referer']])
            command.extend(['-i', source_url])
            
        else:
            # HLS عادي أو مصادر أخرى
            command.extend([
                '-multiple_requests', '1',
                '-reconnect', '1',
                '-reconnect_streamed', '1',
                '-reconnect_at_eof', '1',
                '-reconnect_on_network_error', '1',
                '-reconnect_on_http_error', '4xx,5xx',
                '-reconnect_delay_max', '2',
                '-analyzeduration', '2000000',
                '-probesize', '2000000',
                '-fflags', '+genpts+discardcorrupt+nobuffer+flush_packets',
                '-timeout', '5000000',
                '-rw_timeout', '5000000',
                '-protocol_whitelist', 'file,http,https,tcp,tls,crypto,hls',
                '-tls_verify', '0',
                '-user_agent', headers['User-Agent'],
                '-i', source_url,
            ])
        
        # إضافة اللوجو إن وجد
        if logo_path and os.path.exists(logo_path):
            command.extend(['-i', logo_path])
        
        # ═══════════════════════════════════════════════════════════
        # معاملات الجودة
        # ═══════════════════════════════════════════════════════════
        
        quality_settings = self.get_quality_settings(quality)
        
        # ═══════════════════════════════════════════════════════════
        # معاملات الترميز (OUTPUT)
        # ═══════════════════════════════════════════════════════════
        
        # معاملات الفيديو
        command.extend([
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-profile:v', 'high',
            '-level', '4.1',
            '-b:v', quality_settings['bitrate'],
            '-maxrate', quality_settings['maxrate'],
            '-bufsize', quality_settings['bufsize'],
            '-pix_fmt', 'yuv420p',
            '-g', '60',
            '-keyint_min', '30',
            '-sc_threshold', '0',
            '-force_key_frames', 'expr:gte(t,n_forced*2)',
        ])
        
        # معاملات الصوت
        command.extend([
            '-c:a', 'aac',
            '-b:a', quality_settings['audio_bitrate'],
            '-ar', '44100',
            '-ac', '2',
            '-af', 'aresample=async=1:min_hard_comp=0.100000:first_pts=0',
        ])
        
        # معاملات الإخراج RTMP
        command.extend([
            '-f', 'flv',
            '-flvflags', 'no_duration_filesize+no_metadata',
            '-max_muxing_queue_size', '2048',
            '-flush_packets', '1',
            '-rtmp_buffer', '1500',
            '-rtmp_live', 'live',
            rtmp_url
        ])
        
        return command

    def optimize_periscope_url(self, url):
        """تحسين رابط Periscope للاستقرار"""
        # تحويل من transcode إلى non_transcode للاستقرار
        if 'transcode/' in url and 'dynamic_highlatency.m3u8' in url:
            url = url.replace('/transcode/', '/non_transcode/')
            url = url.replace('dynamic_highlatency.m3u8', 'master_dynamic_highlatency.m3u8')
            logger.info("🔄 تحويل Periscope إلى master playlist")
        
        # إزالة المنفذ الزائد
        url = url.replace(':443/', '/')
        
        return url

    def get_quality_settings(self, quality):
        """الحصول على إعدادات الجودة"""
        settings = {
            'ultra': {
                'bitrate': '5000k',
                'maxrate': '6000k',
                'bufsize': '10000k',
                'audio_bitrate': '192k'
            },
            'high': {
                'bitrate': '4500k',
                'maxrate': '5000k',
                'bufsize': '9000k',
                'audio_bitrate': '160k'
            },
            'medium': {
                'bitrate': '3000k',
                'maxrate': '3500k',
                'bufsize': '6000k',
                'audio_bitrate': '128k'
            },
            'low': {
                'bitrate': '2000k',
                'maxrate': '2500k',
                'bufsize': '4000k',
                'audio_bitrate': '96k'
            }
        }
        return settings.get(quality.lower(), settings['ultra'])

    def validate_source(self, url):
        """التحقق من صلاحية المصدر"""
        try:
            source_type = self.detect_source_type(url)
            headers = self.get_headers_for_source(source_type, url)
            
            response = requests.head(url, headers=headers, timeout=10, verify=False, allow_redirects=True)
            
            if response.status_code == 200:
                return True, source_type
            elif response.status_code == 405:
                # بعض السيرفرات لا تدعم HEAD، نجرب GET
                response = requests.get(url, headers=headers, timeout=10, verify=False, stream=True)
                response.close()
                return response.status_code == 200, source_type
            else:
                return False, source_type
                
        except Exception as e:
            logger.warning(f"⚠️ فشل التحقق من المصدر: {e}")
            return True, self.detect_source_type(url)  # نعتبره صالح ونترك FFmpeg يتعامل

    def start_stream(self, source_url, rtmp_url, stream_key, logo_path=None, quality='ultra'):
        """بدء البث مع تقنيات تجنب الكشف"""
        if self.process and self.process.poll() is None:
            return False, "⚠️ البث يعمل بالفعل!"
        
        self.is_running = False
        self.process = None
        self.reconnect_count = 0
        
        # التحقق من المصدر
        logger.info("🔍 التحقق من المصدر...")
        is_valid, source_type = self.validate_source(source_url)
        
        if not is_valid:
            return False, f"❌ المصدر غير متاح!\n\nتأكد من صلاحية الرابط."
        
        logger.info(f"✅ المصدر متاح ({source_type})")
        
        # تفعيل تقنيات تجنب الكشف
        logger.info("🔐 تفعيل تقنيات تجنب الكشف...")
        self.anti_detect.apply_stream_spacing()
        time.sleep(random.uniform(1, 2))
        
        # بناء الأمر
        command = self.build_ffmpeg_command(source_url, stream_key, logo_path, quality=quality)
        
        logger.info(f"📺 بدء البث...")
        logger.info(f"📍 المصدر: {source_url[:60]}...")
        
        try:
            # تشغيل FFmpeg
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            logger.info(f"✅ FFmpeg بدأ (PID: {self.process.pid})")
            
            # انتظر للتحقق من الاتصال
            time.sleep(5)
            
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate(timeout=2)
                logger.error(f"❌ FFmpeg فشل: {stderr[:500] if stderr else 'No error output'}")
                self.process = None
                
                error_msg = self.parse_ffmpeg_error(stderr)
                return False, error_msg
            
            # انتظر إضافي للتأكد
            time.sleep(5)
            
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate(timeout=2)
                error_msg = self.parse_ffmpeg_error(stderr)
                return False, error_msg
            
            self.is_running = True
            
            # مراقب العملية
            self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
            self.monitor_thread.start()
            
            source_name = {
                'periscope': 'Twitter/Periscope',
                'ts_direct': 'TS مباشر',
                'sports_channel': 'قناة رياضية',
                'hls_standard': 'HLS',
                'mpegts': 'MPEG-TS'
            }.get(source_type, 'عادي')
            
            return True, f"✅ البث يعمل!\n\n📡 النوع: {source_name}\n🛡️ حماية مفعلة\n📺 افتح صفحة البث في Facebook\n⏱️ يجب أن تراه في ثوانٍ\n\nاستخدم /stop لإيقاف البث."
            
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            self.process = None
            return False, f"❌ خطأ: {str(e)}"

    def parse_ffmpeg_error(self, stderr):
        """تحليل أخطاء FFmpeg وترجمتها"""
        if not stderr:
            return "❌ البث فشل!\n\nتأكد من الرابط صحيح."
        
        stderr_lower = stderr.lower()
        
        if "mime type is not rfc8216" in stderr_lower:
            return "❌ صيغة البث غير معيارية!\n\nجرب رابط M3U8 آخر."
        elif "connection refused" in stderr_lower or "refused" in stderr_lower:
            return "❌ فشل الاتصال بـ Facebook!\n\nتأكد من Stream Key صحيح وجديد."
        elif "403" in stderr or "forbidden" in stderr_lower:
            return "❌ الوصول مرفوض!\n\nالرابط محمي أو منتهي الصلاحية."
        elif "404" in stderr or "not found" in stderr_lower:
            return "❌ الرابط غير موجود!\n\nتأكد من صحة الرابط."
        elif "timeout" in stderr_lower:
            return "❌ انتهت مهلة الاتصال!\n\nتحقق من الإنترنت والرابط."
        elif "invalid data" in stderr_lower or "invalid stream" in stderr_lower:
            return "❌ بيانات غير صالحة!\n\nالرابط لا يحتوي على بث صالح."
        elif "no route to host" in stderr_lower:
            return "❌ لا يمكن الوصول للسيرفر!\n\nتحقق من الاتصال بالإنترنت."
        else:
            return f"❌ البث فشل!\n\nتأكد من الرابط صحيح.\n\n{stderr[:200]}"

    def _monitor(self):
        """مراقبة عملية البث مع إعادة اتصال تلقائية"""
        while self.is_running and self.process:
            if self.process.poll() is not None:
                logger.warning("⚠️ البث توقف")
                self.is_running = False
                break
            time.sleep(5)

    def stop_stream(self):
        """إيقاف البث"""
        self.is_running = False
        
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=3)
                except:
                    self.process.kill()
            except:
                pass
            self.process = None
        
        return True, "✅ تم إيقاف البث."

    def get_status(self):
        """حالة البث"""
        if self.process and self.process.poll() is None:
            return {'active': True, 'source_type': self.current_source_type}
        self.is_running = False
        return {'active': False}

    def get_detailed_status(self):
        """حالة مفصلة"""
        status = self.get_status()
        if status['active']:
            source_type_value = status.get('source_type') or ''
            source_names = {
                'periscope': 'Twitter/Periscope',
                'ts_direct': 'TS مباشر',
                'sports_channel': 'قناة رياضية',
                'hls_standard': 'HLS',
                'mpegts': 'MPEG-TS'
            }
            source_name = source_names.get(str(source_type_value), 'عادي')
            return f"✅ البث نشط 🛡️\n📡 النوع: {source_name}\n🔐 حماية: مفعلة"
        return "❌ البث متوقف"

    def parse_m3u8_for_best_quality(self, m3u8_url):
        """تحليل M3U8 واختيار أفضل جودة"""
        source_type = self.detect_source_type(m3u8_url)
        
        # إذا كان TS مباشر، لا نحتاج تحليل
        if source_type == 'ts_direct':
            logger.info("📡 TS مباشر - لا يحتاج تحليل")
            return m3u8_url
        
        try:
            headers = self.get_headers_for_source(source_type, m3u8_url)
            
            response = requests.get(m3u8_url, headers=headers, timeout=15, verify=False)
            response.raise_for_status()
            content = response.text
            
            # إذا لم يكن master playlist
            if '#EXT-X-STREAM-INF' not in content:
                logger.info("📡 Single quality stream")
                return m3u8_url
            
            bitrates = {}
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                if 'EXT-X-STREAM-INF' in line and 'BANDWIDTH=' in line:
                    try:
                        bandwidth = int(line.split('BANDWIDTH=')[1].split(',')[0])
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line and not next_line.startswith('#'):
                                if next_line.startswith('http'):
                                    bitrates[bandwidth] = next_line
                                else:
                                    base_url = m3u8_url.rsplit('/', 1)[0]
                                    bitrates[bandwidth] = urljoin(base_url + '/', next_line)
                    except Exception as e:
                        logger.debug(f"Error parsing bandwidth: {e}")
                        pass
            
            if bitrates:
                best_bandwidth = max(bitrates.keys())
                logger.info(f"🎬 M3U8: {len(bitrates)} جودات، اختيار {best_bandwidth/1000:.0f}k")
                return bitrates[best_bandwidth]
            
        except Exception as e:
            logger.warning(f"⚠️ لم نتمكن من تحليل M3U8: {e}")
        
        return m3u8_url
