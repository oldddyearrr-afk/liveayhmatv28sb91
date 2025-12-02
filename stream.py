import subprocess
import logging
import config
import os
import time
import threading
import random
import requests
from urllib.parse import urljoin
from anti_detection import AntiDetection

logger = logging.getLogger(__name__)

class StreamManager:
    def __init__(self):
        self.process = None
        self.is_running = False
        self.anti_detect = AntiDetection()
        self.monitor_thread = None

    def build_ffmpeg_command(self, m3u8_url, stream_key, logo_path=None, quality='ultra'):
        """بناء أمر FFmpeg مع إعدادات myproject المثبتة"""
        rtmp_url = f"rtmps://live-api-s.facebook.com:443/rtmp/{stream_key}"
        
        # اكتشاف نوع المصدر
        is_periscope = 'pscp.tv' in m3u8_url or 'periscope' in m3u8_url.lower()
        is_ts_stream = '.ts' in m3u8_url or 'mpegts' in m3u8_url.lower()
        
        # تحويل من transcode إلى master للاستقرار
        if is_periscope and 'transcode/' in m3u8_url and 'dynamic_highlatency.m3u8' in m3u8_url:
            m3u8_url = m3u8_url.replace('/transcode/', '/non_transcode/').replace('dynamic_highlatency.m3u8', 'master_dynamic_highlatency.m3u8')
            m3u8_url = m3u8_url.replace(':443/', '/')
            logger.info(f"🔄 تحويل إلى master playlist للاستقرار")
        
        logger.info(f"📊 الجودة: {quality.upper()}")
        logger.info(f"📡 النوع: {'Periscope' if is_periscope else 'آخر'}")
        
        command = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel', 'warning',
        ]
        
        # معاملات الإدخال (INPUT PARAMETERS) - نفس myproject
        if not is_ts_stream:
            command.extend([
                '-multiple_requests', '1',
                '-reconnect', '1',
                '-reconnect_streamed', '1',
                '-reconnect_at_eof', '1',
                '-reconnect_on_network_error', '1',
                '-reconnect_on_http_error', '4xx,5xx',
                '-reconnect_delay_max', '2',
            ])
        
        command.extend([
            '-analyzeduration', '2000000',
            '-probesize', '2000000',
            '-fflags', '+genpts+discardcorrupt+nobuffer+flush_packets',
            '-timeout', '5000000',
            '-rw_timeout', '5000000',
            '-protocol_whitelist', 'file,http,https,tcp,tls,crypto',
            '-tls_verify', '0',
            '-user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            '-i', m3u8_url,
        ])
        
        # إضافة اللوجو إن وجد
        if logo_path and os.path.exists(logo_path):
            command.extend(['-i', logo_path])
        
        # معاملات الجودة (نفس config)
        if quality.lower() == 'ultra':
            bitrate = '5000k'
            maxrate = '6000k'
            bufsize = '10000k'
            audio_bitrate = '192k'
        elif quality.lower() == 'high':
            bitrate = '4500k'
            maxrate = '5000k'
            bufsize = '9000k'
            audio_bitrate = '160k'
        elif quality.lower() == 'medium':
            bitrate = '3000k'
            maxrate = '3500k'
            bufsize = '6000k'
            audio_bitrate = '128k'
        else:
            bitrate = '2000k'
            maxrate = '2500k'
            bufsize = '4000k'
            audio_bitrate = '96k'
        
        # معاملات الترميز (OUTPUT PARAMETERS)
        command.extend([
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-b:v', bitrate,
            '-maxrate', maxrate,
            '-bufsize', bufsize,
            '-pix_fmt', 'yuv420p',
            '-g', '60',
            '-keyint_min', '30',
            '-sc_threshold', '0',
            '-c:a', 'aac',
            '-b:a', audio_bitrate,
            '-ar', '44100',
            '-ac', '2',
            '-f', 'flv',
            '-flvflags', 'no_duration_filesize+no_metadata',
            '-max_muxing_queue_size', '1024',
            '-flush_packets', '1',
            '-rtmp_buffer', '1000',
            '-rtmp_live', 'live',
            rtmp_url
        ])
        
        return command

    def start_stream(self, m3u8_url, rtmp_url, stream_key, logo_path=None, quality='ultra'):
        """بدء البث مع تقنيات تجنب الكشف"""
        if self.process and self.process.poll() is None:
            return False, "⚠️ البث يعمل بالفعل!"
        
        self.is_running = False
        self.process = None
        
        logger.info("🔐 تفعيل تقنيات تجنب الكشف...")
        self.anti_detect.apply_stream_spacing()
        time.sleep(random.uniform(1, 3))
        
        command = self.build_ffmpeg_command(m3u8_url, stream_key, logo_path, quality=quality)
        
        logger.info(f"📺 بدء البث...")
        logger.info(f"📍 المصدر: {m3u8_url[:50]}...")
        
        try:
            # تشغيل FFmpeg في الخلفية
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            logger.info(f"✅ FFmpeg بدأ (PID: {self.process.pid})")
            
            # انتظر 5 ثواني للتحقق من الاتصال
            time.sleep(5)
            
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate(timeout=1)
                logger.error(f"❌ FFmpeg فشل: {stderr[:300]}")
                self.process = None
                
                if "mime type is not rfc8216" in stderr:
                    return False, "❌ صيغة البث غير معيارية!"
                elif "Connection refused" in stderr or "refused" in stderr.lower():
                    return False, "❌ فشل الاتصال بـ Facebook!\n\nتأكد من Stream Key صحيح."
                else:
                    return False, "❌ البث فشل!\n\nتأكد من الرابط صحيح."
            
            # انتظر 5 ثواني إضافية
            time.sleep(5)
            
            if self.process.poll() is not None:
                return False, "❌ البث توقف بعد البدء!"
            
            self.is_running = True
            
            # مراقب العملية
            self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
            self.monitor_thread.start()
            
            return True, "✅ البث يعمل!\n\n🛡️ حماية مفعلة\n📺 افتح صفحة البث في Facebook\n⏱️ يجب أن تراه في ثوانٍ\n\nاستخدم /stop لإيقاف البث."
            
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            self.process = None
            return False, f"❌ خطأ: {str(e)}"

    def _monitor(self):
        """مراقبة عملية البث"""
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
            return {'active': True}
        self.is_running = False
        return {'active': False}

    def get_detailed_status(self):
        """حالة مفصلة"""
        status = self.get_status()
        if status['active']:
            return "✅ البث نشط 🛡️\n🔐 حماية: مفعلة"
        return "❌ البث متوقف"

    def parse_m3u8_for_best_quality(self, m3u8_url):
        """تحليل M3U8 واختيار أفضل جودة"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://pscp.tv/',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(m3u8_url, headers=headers, timeout=10, verify=False)
            response.raise_for_status()
            content = response.text
            
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
                    except:
                        pass
            
            if bitrates:
                best_bandwidth = max(bitrates.keys())
                logger.info(f"🎬 M3U8: {len(bitrates)} جودات، اختيار {best_bandwidth/1000:.0f}k")
                return bitrates[best_bandwidth]
            
        except Exception as e:
            logger.warning(f"⚠️ لم نتمكن من تحليل M3U8: {e}")
        
        return m3u8_url
