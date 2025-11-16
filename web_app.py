
#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, request, send_from_directory
import subprocess
import os
import json
import re
from datetime import datetime

app = Flask(__name__)

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

def parse_config():
    """Parse config.sh to get logo settings"""
    config = {
        'logo_enabled': False,
        'logo_path': 'channel_logo.png',
        'logo_position': 'topright',
        'logo_size': '350:-1',
        'logo_opacity': '0.95',
        'logo_offset_x': '20',
        'logo_offset_y': '20',
        'streaming_mode': 'encode'
    }
    
    try:
        with open('config.sh', 'r', encoding='utf-8') as f:
            content = f.read()
            
            patterns = {
                'logo_enabled': r'LOGO_ENABLED="([^"]+)"',
                'logo_path': r'LOGO_PATH="([^"]+)"',
                'logo_position': r'LOGO_POSITION="([^"]+)"',
                'logo_size': r'LOGO_SIZE="([^"]*)"',
                'logo_opacity': r'LOGO_OPACITY="([^"]+)"',
                'logo_offset_x': r'LOGO_OFFSET_X="([^"]+)"',
                'logo_offset_y': r'LOGO_OFFSET_Y="([^"]+)"',
                'streaming_mode': r'STREAMING_MODE="([^"]+)"'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    config[key] = match.group(1)
        
        config['logo_enabled'] = config['logo_enabled'].lower() == 'true'
        
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
    try:
        # Check if already running
        if get_stream_status():
            # Stop first
            subprocess.run(['bash', 'control.sh', 'stop'], check=False)
            import time
            time.sleep(2)
        
        # Start stream directly using main.sh in background
        # This avoids the issue with control.sh waiting
        subprocess.Popen(
            ['bash', '-c', 'source config.sh && bash main.sh &'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Give it a moment to start
        import time
        time.sleep(3)
        
        # Verify it started
        if get_stream_status():
            return jsonify({'success': True, 'message': 'Stream started'})
        else:
            return jsonify({'success': False, 'error': 'Stream failed to start - check secrets and config'}), 500
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
        
        logo_exists = os.path.exists(config['logo_path'])
        config['logo_exists'] = logo_exists
        
        if logo_exists:
            config['logo_url'] = f"/logo/{os.path.basename(config['logo_path'])}"
        else:
            config['logo_url'] = None
            
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logo/<path:filename>')
def serve_logo(filename):
    logo_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(logo_dir, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
