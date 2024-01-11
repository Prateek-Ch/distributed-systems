import socket

HOST = socket.gethostbyname(socket.gethostname())
PORT = 9090
HEADER = 8
FORMAT = 'utf-8'

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))
        
def start():
    print(f"Server listening on {HOST}:{PORT}")
    while True:
        data, address = server.recvfrom(1024)
        message = data.decode(FORMAT)
        print(f"Message from {address}: {message}")
        server.sendto('Got your message'.encode(FORMAT), address) 
        
print("Server is starting...")
start()