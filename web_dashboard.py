#!/usr/bin/env python3
import os
import subprocess
from flask import Flask, render_template_string, jsonify, request
import json

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم البث - Facebook Live</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #667eea;
            margin-bottom: 20px;
            text-align: center;
            font-size: 2.5em;
        }
        .status {
            text-align: center;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 1.3em;
            font-weight: bold;
        }
        .status.running { background: #d4edda; color: #155724; }
        .status.stopped { background: #f8d7da; color: #721c24; }
        .buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        button {
            padding: 15px 25px;
            font-size: 16px;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            color: white;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .btn-start { background: #28a745; }
        .btn-stop { background: #dc3545; }
        .btn-restart { background: #ffc107; color: #333; }
        .btn-status { background: #17a2b8; }
        .btn-logs { background: #6c757d; }
        .info-box {
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }
        .info-box h3 { color: #2196F3; margin-bottom: 10px; }
        .manual-extract {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }
        .manual-extract h3 { color: #856404; margin-bottom: 10px; }
        .manual-extract ol { margin-right: 20px; margin-top: 10px; }
        .manual-extract li { margin: 8px 0; }
        .code {
            background: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            margin: 10px 0;
            direction: ltr;
            text-align: left;
        }
        #response {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            display: none;
        }
        #response.success { background: #d4edda; color: #155724; display: block; }
        #response.error { background: #f8d7da; color: #721c24; display: block; }
        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }
        .loading.active { display: block; }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🎥 لوحة تحكم البث المباشر</h1>
            
            <div id="status" class="status stopped">
                ⏸️ البث متوقف
            </div>

            <div class="buttons">
                <button class="btn-start" onclick="controlStream('start')">▶️ بدء البث</button>
                <button class="btn-stop" onclick="controlStream('stop')">⏹️ إيقاف البث</button>
                <button class="btn-restart" onclick="controlStream('restart')">🔄 إعادة تشغيل</button>
                <button class="btn-status" onclick="checkStatus()">📊 تحديث الحالة</button>
                <button class="btn-logs" onclick="showLogs()">📝 عرض السجلات</button>
            </div>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>جاري التنفيذ...</p>
            </div>

            <div id="response"></div>
        </div>

        <div class="card">
            <div class="manual-extract">
                <h3>⚠️ طريقة استخراج رابط فيسبوك يدوياً</h3>
                <p><strong>ملاحظة:</strong> استخراج الرابط التلقائي من فيسبوك لا يعمل حالياً. استخدم الطريقة اليدوية:</p>
                <ol>
                    <li>افتح رابط البث في متصفح Chrome أو Firefox</li>
                    <li>اضغط <code>F12</code> لفتح أدوات المطور</li>
                    <li>اذهب لتبويب <strong>Network</strong> (الشبكة)</li>
                    <li>في مربع البحث اكتب: <code>.m3u8</code></li>
                    <li>اضغط <code>F5</code> لتحديث الصفحة أو شغل الفيديو</li>
                    <li>اضغط بيمين الفأرة على ملف <code>.m3u8</code></li>
                    <li>اختر <strong>Copy → Copy URL</strong></li>
                    <li>استخدم الرابط في ملف <code>config.sh</code></li>
                </ol>
                <div class="code">
                    مثال الرابط المطلوب:<br>
                    https://video.xx.fbcdn.net/hvideo-xxx/v/xxx.m3u8?token=...
                </div>
            </div>
        </div>

        <div class="card">
            <div class="info-box">
                <h3>ℹ️ معلومات مهمة</h3>
                <ul style="margin-right: 20px;">
                    <li>تأكد من ضبط <code>FB_STREAM_KEY</code> في المتغيرات البيئية</li>
                    <li>تأكد من تحديث <code>SOURCE</code> في ملف <code>config.sh</code></li>
                    <li>الجودة الحالية: <strong>Ultra (1080p @ 30fps)</strong></li>
                    <li>يمكنك تغيير الجودة من ملف <code>config.sh</code></li>
                </ul>
            </div>
        </div>
    </div>

    <script>
        function showLoading() {
            document.getElementById('loading').classList.add('active');
            document.getElementById('response').style.display = 'none';
        }

        function hideLoading() {
            document.getElementById('loading').classList.remove('active');
        }

        function showResponse(message, type) {
            const responseDiv = document.getElementById('response');
            responseDiv.textContent = message;
            responseDiv.className = type;
        }

        async function checkStatus() {
            showLoading();
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                hideLoading();
                
                const statusDiv = document.getElementById('status');
                if (data.status === 'running') {
                    statusDiv.className = 'status running';
                    statusDiv.textContent = '🔴 البث شغال الآن';
                } else {
                    statusDiv.className = 'status stopped';
                    statusDiv.textContent = '⏸️ البث متوقف';
                }
                
                showResponse(data.message, 'success');
            } catch (error) {
                hideLoading();
                showResponse('خطأ في الاتصال: ' + error, 'error');
            }
        }

        async function controlStream(action) {
            showLoading();
            try {
                const response = await fetch('/api/control', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action: action})
                });
                const data = await response.json();
                hideLoading();
                
                showResponse(data.message, data.success ? 'success' : 'error');
                
                setTimeout(checkStatus, 2000);
            } catch (error) {
                hideLoading();
                showResponse('خطأ: ' + error, 'error');
            }
        }

        async function showLogs() {
            showLoading();
            try {
                const response = await fetch('/api/logs');
                const data = await response.json();
                hideLoading();
                
                showResponse(data.logs || data.message, data.success ? 'success' : 'error');
            } catch (error) {
                hideLoading();
                showResponse('خطأ: ' + error, 'error');
            }
        }

        checkStatus();
        setInterval(checkStatus, 10000);
    </script>
</body>
</html>
"""

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def get_status():
    success, output = run_command('bash control.sh status 2>&1 | tail -20')
    is_running = 'RUNNING' in output or 'running' in output.lower()
    
    return jsonify({
        'status': 'running' if is_running else 'stopped',
        'message': output if output else 'لا توجد معلومات متاحة',
        'success': True
    })

@app.route('/api/control', methods=['POST'])
def control_stream():
    data = request.get_json()
    action = data.get('action', '')
    
    if action not in ['start', 'stop', 'restart']:
        return jsonify({'success': False, 'message': 'إجراء غير صالح'})
    
    success, output = run_command(f'bash control.sh {action} 2>&1')
    
    return jsonify({
        'success': success,
        'message': output if output else f'تم {action} بنجاح'
    })

@app.route('/api/logs')
def get_logs():
    success, output = run_command('bash control.sh logs 2>&1')
    
    return jsonify({
        'success': success,
        'logs': output if output else 'لا توجد سجلات متاحة'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
