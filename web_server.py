from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from socketserver import ThreadingMixIn
import socketserver
import threading
import cv2
import time
from PIL import Image

PORT = 8090

def create_servers():
    class TCPServerRequest(socketserver.BaseRequestHandler):
        def handle(self):
            # Handle is called each time a client is connected
            # When OpenDataCam connects, do not return - instead keep the connection open and keep streaming data
            # First send HTTP header
            header = 'HTTP/1.0 200 OK\r\nServer: Mozarella/2.2\r\nAccept-Range: bytes\r\nConnection: close\r\nMax-Age: 0\r\nExpires: 0\r\nCache-Control: no-cache, private\r\nPragma: no-cache\r\nContent-Type: application/json\r\n\r\n'
            self.request.send(header.encode())
            while True:
                time.sleep(0.1)
                if hasattr(self.server, 'datatosend'):
                    self.request.send(self.server.datatosend.encode() + "\r\n".encode())
    
    class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
        pass

    class MyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            while True:
                if hasattr(self.server, "frametosend"):
                    frame = self.server.frametosend
                    frame *= 6
                    _, jpg = cv2.imencode(".jpg", frame)
                    jpg_bytes = jpg.tobytes()
                    self.wfile.write("--jpgboundary".encode())
                    self.send_header('Content-type', 'image/jpeg')
                    self.send_header('Content-length', len(jpg_bytes))
                    self.end_headers()
                    self.wfile.write(jpg_bytes)
                    time.sleep(0.1)

    tcpd = socketserver.TCPServer(('localhost', 8070), TCPServerRequest)
    th = threading.Thread(target=tcpd.serve_forever)
    th.daemon = True
    th.start()

    httpd = ThreadingHTTPServer(("localhost", PORT), MyHandler)
    th2 = threading.Thread(target=httpd.serve_forever)
    th2.daemon = True
    th2.start()

    return tcpd, httpd

def get_webcam_stream():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    return cap

def main():
    try:
        tcpd, httpd = create_servers()
        
        cap = get_webcam_stream()
        while True:
            ret, frame = cap.read()
            tcpd.datatosend = "GJ"
            httpd.frametosend = frame
    except KeyboardInterrupt:
        cap.release()
        tcpd.server_close()
        httpd.server_close()

if __name__ == "__main__":
    main()