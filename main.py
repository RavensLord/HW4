from datetime import datetime
import json
import mimetypes
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.parse
import socket


UPD_IP = "127.0.0.1"
UPD_PORT = 5000


class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        print(data_dict)
        send_to_socket_server(data_dict)
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()


    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message":
            self.send_html_file("message.html")
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("error.html", 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())


def send_to_socket_server(data_dict):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = urllib.parse.urlencode(data_dict)
    sock.sendto(message.encode('utf-8'), (UPD_IP, UPD_PORT))
    

def run_http(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("0.0.0.0", 3000) #127.0.0.1
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()
        

def run_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UPD_IP, UPD_PORT))

    try:
        while True:
            data, address = sock.recvfrom(1024)
            data_parse = urllib.parse.parse_qs(data.decode('utf-8'))
            data_dict = {key: value[0] for key, value in data_parse.items()}
            save_to_json(data_dict)
            
    except KeyboardInterrupt:
        print(f'Destroy server')
    finally:
        sock.close()


def save_to_json(data):
    file_path = pathlib.Path("storage/data.json")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not file_path.exists():
        with open(file_path, "w") as file:
            json.dump({}, file)
    
    with open(file_path, "r") as file:
        try:
            jdata = json.load(file)
        except:
            jdata = {}
    
    jdata[str(datetime.now())] = data

    with open(file_path, "w") as file:
        json.dump(jdata, file, indent=4)


if __name__ == '__main__':
    socket_server = threading.Thread(target=run_socket)
    http_server = threading.Thread(target=run_http)
    
    http_server.start()
    socket_server.start()
    
    http_server.join()
    socket_server.join()