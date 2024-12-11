# https://support.huaweicloud.com/api-sis/sis_03_0058.html

import http.server
import ssl
import random
import string

class TokenServer(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        # 获取客户端的IP地址和端口号
        client_ip, client_port = self.client_address

        if self.path == '/v3/auth/tokens':
            # 获取请求的内容长度并读取请求体
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            # 检查请求体是否包含 'identity' 字样
            if b'identity' in post_data:
                # 生成长度为128的随机字符串作为token
                token = ''.join(random.choices(string.ascii_letters + string.digits, k=128))

                # 设置响应头部，返回token在X-Subject-Token中 
                self.send_response(200)
                self.send_header('X-Subject-Token', token)
                self.end_headers()

                # 可选：返回一些响应内容（例如JSON格式）
                response_content = b'{"message": "Token generated successfully"}'

                # 写入响应内容（可选）
                self.wfile.write(response_content)
                
                print(f'Token generated for client {client_ip}:{client_port}')

            else:
                # 如果没有包含'identity', 返回400错误 
                self.send_response(400)
                self.end_headers()
                response_content = b'{"error": "Invalid request."}'
                self.wfile.write(response_content)
        else:
            # 如果访问了其他路径，返回404错误 
            self.send_response(404)
            self.end_headers()
            response_content = b'{"error": "Not Found."}'
            self.wfile.write(response_content)


def run(server_class=http.server.HTTPServer, port=4443):
    server_address = ('', port)
    httpd = server_class(server_address, TokenServer)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile='./libwebsockets-test-server.pem',
                            keyfile='./libwebsockets-test-server.key.pem')
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    print(f'Serving on https://0.0.0.0:{port}')
    httpd.serve_forever()


if __name__ == "__main__":
    run()
