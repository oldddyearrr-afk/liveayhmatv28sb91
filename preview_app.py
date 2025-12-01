#!/usr/bin/env python3
import http.server
import socketserver
import os
import json
import config

PORT = 5000
socketserver.TCPServer.allow_reuse_address = True

class PreviewHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            with open('templates/preview.html', 'r', encoding='utf-8') as f:
                self.wfile.write(f.read().encode('utf-8'))
        elif self.path == '/api/config':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            size_value = 150
            if isinstance(config.LOGO_SIZE, str) and ':' in config.LOGO_SIZE:
                try:
                    size_value = int(config.LOGO_SIZE.split(':')[0])
                except:
                    pass
            else:
                try:
                    size_value = int(config.LOGO_SIZE)
                except:
                    pass
            
            opacity_value = 1.0
            try:
                opacity_value = float(config.LOGO_OPACITY)
            except:
                pass
            
            data = {
                'offset_x': config.LOGO_OFFSET_X,
                'offset_y': config.LOGO_OFFSET_Y,
                'size': size_value,
                'opacity': opacity_value
            }
            self.wfile.write(json.dumps(data).encode('utf-8'))
        elif self.path.startswith('/static/'):
            file_path = self.path[1:]
            if os.path.exists(file_path):
                self.send_response(200)
                if file_path.endswith('.png'):
                    self.send_header('Content-type', 'image/png')
                elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                    self.send_header('Content-type', 'image/jpeg')
                else:
                    self.send_header('Content-type', 'application/octet-stream')
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with socketserver.TCPServer(("0.0.0.0", PORT), PreviewHandler) as httpd:
        print(f"معاينة اللوجو تعمل على http://0.0.0.0:{PORT}")
        httpd.serve_forever()
