
#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, request, send_from_directory
import subprocess
import os
import json
import re
from datetime import datetime

app = Flask(__name__)

STATUS_FILE = "/tmp/fbstream_status.txt"

def get_stream_status():
    """Check if stream is running"""
    try:
        result = subprocess.run(
            ['tmux', 'has-session', '-t', 'fbstream'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False

def get_detailed_status():
    """Get detailed stream status from status file"""
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, 'r') as f:
                content = f.read().strip()
                parts = content.split('|')
                if len(parts) >= 2:
                    return {
                        'state': parts[0],
                        'message': parts[1],
                        'timestamp': int(parts[2]) if len(parts) > 2 else None
                    }
        return {'state': 'UNKNOWN', 'message': 'No status file', 'timestamp': None}
    except Exception as e:
        return {'state': 'ERROR', 'message': str(e), 'timestamp': None}

def parse_config():
    """Parse config.sh to get watermark settings"""
    config = {
        'watermark_enabled': False,
        'watermark_text': 'Your Channel Name',
        'watermark_fontsize': '30',
        'watermark_fontcolor': 'white@0.85',
        'watermark_y_offset': '40',
        'watermark_scroll_speed': '120',
        'streaming_mode': 'encode'
    }
    
    try:
        with open('config.sh', 'r', encoding='utf-8') as f:
            content = f.read()
            
            patterns = {
                'watermark_enabled': r'WATERMARK_ENABLED="([^"]+)"',
                'watermark_text': r'WATERMARK_TEXT="([^"]+)"',
                'watermark_fontsize': r'WATERMARK_FONTSIZE="([^"]+)"',
                'watermark_fontcolor': r'WATERMARK_FONTCOLOR="([^"]+)"',
                'watermark_y_offset': r'WATERMARK_Y_OFFSET="([^"]+)"',
                'watermark_scroll_speed': r'WATERMARK_SCROLL_SPEED="([^"]+)"',
                'streaming_mode': r'STREAMING_MODE="([^"]+)"'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    config[key] = match.group(1)
        
        config['watermark_enabled'] = config['watermark_enabled'].lower() == 'true'
        
    except Exception as e:
        print(f"Error parsing config: {e}")
    
    return config

def get_stream_info():
    """Get stream information"""
    status = get_stream_status()
    
    info = {
        'status': 'running' if status else 'stopped',
        'uptime': None,
        'log_file': None
    }
    
    if status:
        # Get uptime
        try:
            result = subprocess.run(
                ['tmux', 'display-message', '-t', 'fbstream', '-p', '#{session_created}'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                info['uptime'] = result.stdout.strip()
        except:
            pass
    
    # Get latest log file
    if os.path.exists('logs'):
        logs = [f for f in os.listdir('logs') if f.endswith('.log')]
        if logs:
            info['log_file'] = max(logs)
    
    return info

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    return jsonify(get_stream_info())

@app.route('/api/start', methods=['POST'])
def api_start():
    import time
    try:
        # Get stream key from request
        data = request.get_json() or {}
        stream_key = data.get('stream_key', '').strip()
        
        if not stream_key:
            return jsonify({'success': False, 'error': 'Stream Key is required'}), 400
        
        # Check if already running and stop it immediately
        if get_stream_status():
            subprocess.run(['tmux', 'kill-session', '-t', 'fbstream'], 
                         check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5)
        
        # Clear old status file
        if os.path.exists(STATUS_FILE):
            os.remove(STATUS_FILE)
        
        # Clean up old logs in background (non-blocking)
        if os.path.exists('cleanup_logs.sh'):
            subprocess.Popen(['bash', 'cleanup_logs.sh'], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Prepare environment with stream key
        env = os.environ.copy()
        env['FB_STREAM_KEY'] = stream_key
        
        # Start stream directly using main.sh (inherit stdio to avoid buffer blocking)
        process = subprocess.Popen(
            ['bash', 'main.sh'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=env
        )
        
        # Wait for status file to report STREAMING or FAILED (max 20 seconds)
        for i in range(40):
            time.sleep(0.5)
            status = get_detailed_status()
            
            if status['state'] == 'STREAMING':
                return jsonify({'success': True, 'message': 'Stream started successfully'})
            elif status['state'] == 'FAILED':
                return jsonify({'success': False, 'error': status['message']}), 500
        
        # Timeout: check final state
        final_status = get_detailed_status()
        if final_status['state'] == 'STREAMING':
            return jsonify({'success': True, 'message': 'Stream started'})
        else:
            error_msg = final_status.get('message', 'Timeout waiting for stream') if final_status['state'] != 'UNKNOWN' else 'Stream startup timed out'
            return jsonify({'success': False, 'error': error_msg}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def api_stop():
    try:
        subprocess.run(['bash', 'control.sh', 'stop'], check=True)
        return jsonify({'success': True, 'message': 'Stream stopped'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logs')
def api_logs():
    try:
        info = get_stream_info()
        if info['log_file']:
            log_path = os.path.join('logs', info['log_file'])
            with open(log_path, 'r') as f:
                lines = f.readlines()
                return jsonify({'logs': lines[-50:]})
        return jsonify({'logs': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logo-config')
def api_logo_config():
    try:
        config = parse_config()
        # Keep watermark info for UI
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logo/<path:filename>')
def serve_logo(filename):
    logo_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(logo_dir, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
