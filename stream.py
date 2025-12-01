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
        self.tmux_session = "fbstream"
        self.is_running = False
        self.anti_detect = AntiDetection()
        self.stop_event = threading.Event()

    def execute_tmux_cmd(self, cmd_list):
        """Execute shell command via tmux safely"""
        try:
            result = subprocess.run(cmd_list, capture_output=True, text=True, timeout=5)
            return result.stdout.strip()
        except:
            return ""

    def kill_old_session(self):
        """Kill any existing tmux session"""
        try:
            subprocess.run(['tmux', 'kill-session', '-t', self.tmux_session], 
                         capture_output=True, timeout=3)
        except:
            pass
        time.sleep(0.5)

    def build_ffmpeg_command(self, m3u8_url, stream_key, logo_path=None, quality='high'):
        """Build FFmpeg command using working parameters from reference project"""
        rtmp_url = f"rtmps://live-api-s.facebook.com:443/rtmp/{stream_key}"
        
        # Detect source type
        is_periscope = 'pscp.tv' in m3u8_url or 'periscope' in m3u8_url.lower()
        is_ts_stream = '.ts' in m3u8_url or 'mpegts' in m3u8_url.lower()
        
        # Convert transcoded quality to master playlist for stability
        if is_periscope and 'transcode/' in m3u8_url and 'dynamic_highlatency.m3u8' in m3u8_url:
            m3u8_url = m3u8_url.replace('/transcode/', '/non_transcode/').replace('dynamic_highlatency.m3u8', 'master_dynamic_highlatency.m3u8')
            m3u8_url = m3u8_url.replace(':443/', '/')
            logger.info(f"🔄 Converted to master playlist for stability")
        
        logger.info(f"📊 Quality: {quality.upper()}")
        logger.info(f"📡 Source: {'Periscope' if is_periscope else 'Other'}")
        
        # Build input parameters (before -i)
        input_params = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel', 'warning',
        ]
        
        # Fast reconnection settings (like reference project)
        if not is_ts_stream:
            input_params.extend([
                '-multiple_requests', '1',
                '-reconnect', '1',
                '-reconnect_streamed', '1',
                '-reconnect_at_eof', '1',
                '-reconnect_on_network_error', '1',
                '-reconnect_on_http_error', '4xx,5xx',
                '-reconnect_delay_max', '2',
            ])
        
        # Fast analysis
        input_params.extend([
            '-analyzeduration', '2000000',
            '-probesize', '2000000',
            '-fflags', '+genpts+discardcorrupt+nobuffer+flush_packets',
        ])
        
        # Timeouts
        input_params.extend([
            '-timeout', '5000000',
            '-rw_timeout', '5000000',
            '-protocol_whitelist', 'file,http,https,tcp,tls,crypto',
            '-tls_verify', '0',
            '-user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            '-headers', 'Referer: https://pscp.tv/\r\nConnection: keep-alive\r\n',
            
            '-i', m3u8_url,
        ])
        
        # Add logo if provided
        logo_filters = ""
        if logo_path and os.path.exists(logo_path):
            input_params.extend(['-i', logo_path])
            try:
                x_offset = int(str(config.LOGO_OFFSET_X).strip().strip('"').strip("'"))
                y_offset = int(str(config.LOGO_OFFSET_Y).strip().strip('"').strip("'"))
                logo_size = config.LOGO_SIZE or "480:-1"
                
                # Position calculation
                position_filter = f"x=W-w+{x_offset}:y={y_offset}"
                logo_filters = f"-filter_complex \"[1:v]scale={logo_size}[logo];[0:v][logo]overlay={position_filter}\" -map \"[v]:0\" -map \"0:a:0?\""
            except:
                logo_path = None
        
        # Quality settings based on mode (نفس إعدادات myproject)
        if quality.lower() == 'ultra':
            bitrate = config.ULTRA_BITRATE or '5000k'
            maxrate = config.ULTRA_MAXRATE or '6000k'
            bufsize = config.ULTRA_BUFSIZE or '10000k'
            audio_bitrate = config.ULTRA_AUDIO_BITRATE or '192k'
        elif quality.lower() == 'high':
            bitrate = config.HIGH_BITRATE or '4500k'
            maxrate = config.HIGH_MAXRATE or '5000k'
            bufsize = config.HIGH_BUFSIZE or '9000k'
            audio_bitrate = config.HIGH_AUDIO_BITRATE or '160k'
        elif quality.lower() == 'medium':
            bitrate = config.MEDIUM_BITRATE or '3000k'
            maxrate = config.MEDIUM_MAXRATE or '3500k'
            bufsize = config.MEDIUM_BUFSIZE or '6000k'
            audio_bitrate = config.MEDIUM_AUDIO_BITRATE or '128k'
        else:  # low
            bitrate = config.LOW_BITRATE or '2000k'
            maxrate = config.LOW_MAXRATE or '2500k'
            bufsize = config.LOW_BUFSIZE or '4000k'
            audio_bitrate = config.LOW_AUDIO_BITRATE or '96k'
        
        # Encoding parameters (إعدادات myproject المثبتة)
        encode_params = [
            '-c:v', 'libx264',
            '-preset', config.PRESET or 'ultrafast',
            '-tune', config.TUNE or 'zerolatency',
            '-b:v', bitrate,
            '-maxrate', maxrate,
            '-bufsize', bufsize,
            '-pix_fmt', config.PIXEL_FORMAT or 'yuv420p',
            '-g', '60',
            '-keyint_min', '30',
            '-sc_threshold', '0',
            
            '-c:a', config.AUDIO_CODEC or 'aac',
            '-b:a', audio_bitrate,
            '-ar', str(config.AUDIO_RATE or 44100),
            '-ac', '2',
            
            '-f', 'flv',
            '-flvflags', 'no_duration_filesize+no_metadata',
            '-max_muxing_queue_size', '1024',
            '-flush_packets', '1',
            '-rtmp_buffer', '1000',
            '-rtmp_live', 'live',
            
            rtmp_url
        ]
        
        # Combine all parts
        full_cmd = input_params + encode_params
        
        return full_cmd

    def start_stream(self, m3u8_url, rtmp_url, stream_key, logo_path=None, quality='high'):
        """Start streaming using tmux (like reference project)"""
        if self.is_running:
            return False, "⚠️ Stream already running! Use /stop first."
        
        logger.info("🔐 Enabling anti-detection measures...")
        self.anti_detect.apply_stream_spacing()
        time.sleep(random.uniform(1, 3))
        
        # Kill old session
        self.kill_old_session()
        time.sleep(1)
        
        command = self.build_ffmpeg_command(m3u8_url, stream_key, logo_path, quality=quality)
        logger.info(f"📺 Starting stream...")
        logger.info(f"📍 Source: {m3u8_url[:50]}...")
        
        try:
            # Create temp script
            temp_script = f"/tmp/fbstream_{os.getpid()}.sh"
            with open(temp_script, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write(f"{' '.join(command)} 2>&1\n")
            os.chmod(temp_script, 0o755)
            
            # Create tmux session with script
            subprocess.run(
                ['tmux', 'new-session', '-d', '-s', self.tmux_session, temp_script],
                capture_output=True,
                timeout=5
            )
            
            logger.info("✅ FFmpeg session created")
            
            # Wait and verify
            time.sleep(3)
            
            # Check if session still running
            result = subprocess.run(
                ['tmux', 'has-session', '-t', self.tmux_session],
                capture_output=True
            )
            
            if result.returncode != 0:
                logger.error("❌ FFmpeg session died immediately!")
                return False, "❌ Stream failed to start!\n\nCheck Stream Key and Facebook Live settings."
            
            # Wait more to verify actual connection
            time.sleep(5)
            
            # Check again
            result = subprocess.run(
                ['tmux', 'has-session', '-t', self.tmux_session],
                capture_output=True
            )
            
            if result.returncode != 0:
                logger.error("❌ FFmpeg stopped after initial connection!")
                return False, "❌ Stream stopped after starting!\n\nCheck Stream Key validity."
            
            self.is_running = True
            self.stop_event.clear()
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self.monitor_stream, daemon=True)
            monitor_thread.start()
            
            return True, "✅ Stream started!\n\n🛡️ Anti-detection enabled\n📺 Open Facebook Live page\n⏱️ Video should appear in seconds\n\nUse /stop to stop stream."
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            self.kill_old_session()
            return False, f"❌ Error: {str(e)}"

    def monitor_stream(self):
        """Monitor stream and keep it alive"""
        while self.is_running and not self.stop_event.is_set():
            try:
                result = subprocess.run(
                    ['tmux', 'has-session', '-t', self.tmux_session],
                    capture_output=True,
                    timeout=2
                )
                
                if result.returncode != 0:
                    # Session died
                    logger.warning("⚠️ Stream session lost!")
                    self.is_running = False
                    break
                
                time.sleep(5)
            except:
                self.is_running = False
                break

    def stop_stream(self):
        """Stop the stream"""
        self.is_running = False
        self.stop_event.set()
        
        self.kill_old_session()
        time.sleep(0.5)
        
        return True, "✅ Stream stopped."

    def get_status(self):
        """Get stream status"""
        if not self.is_running:
            return {'active': False}
        
        # Check if tmux session exists
        result = subprocess.run(
            ['tmux', 'has-session', '-t', self.tmux_session],
            capture_output=True
        )
        
        active = result.returncode == 0
        if not active:
            self.is_running = False
        
        return {'active': active}

    def get_detailed_status(self):
        """Get detailed status message"""
        status = self.get_status()
        if status['active']:
            return "✅ Stream active 🛡️\n🔐 Anti-detection: enabled"
        return "❌ Stream stopped"

    def parse_m3u8_for_best_quality(self, m3u8_url):
        """Parse M3U8 and select best quality"""
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
                logger.info(f"🎬 M3U8 analysis: found {len(bitrates)} qualities, selected {best_bandwidth/1000:.0f}k")
                return bitrates[best_bandwidth]
            
        except Exception as e:
            logger.warning(f"⚠️ Could not parse M3U8: {e}")
        
        return m3u8_url
