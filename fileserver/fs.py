from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import os

class SimpleFileHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 读取请求内容长度
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode()
            
            # 解析POST参数
            params = parse_qs(post_data)
            
            # 获取文件名和内容
            filename = params.get('filename', [''])[0].strip()
            filecontent = params.get('filecontent', [''])[0]

            # 验证参数
            if not filename or not filecontent:
                self.send_error(400, "Both filename and filecontent are required")
                return

            # 创建上传目录
            upload_dir = 'uploads'
            os.makedirs(upload_dir, exist_ok=True)

            # 过滤安全文件名
            safe_filename = os.path.basename(filename)
            if not safe_filename:
                self.send_error(400, "Invalid filename")
                return

            # 保存文件
            save_path = os.path.join(upload_dir, safe_filename)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(filecontent)

            # 返回响应
            self.send_response(201)
            self.send_header('Content-type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(f"File '{safe_filename}' saved successfully".encode())
            
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")

def run_server(port=8080):
    server = HTTPServer(('0.0.0.0', port), SimpleFileHandler)
    print(f"Server running on port {port}")
    server.serve_forever()

if __name__ == '__main__':
    run_server()