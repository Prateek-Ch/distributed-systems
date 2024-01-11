import socket
from helper import create_segments

HOST = socket.gethostbyname(socket.gethostname())
PORT = 9090
HEADER = 8
FORMAT = 'utf-8'
AVAILABLE = 'available'

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))

addresses = []

def distribute_tasks(addresses, data):
    segments = create_segments(data, len(addresses))
    print(segments)
    for segment, address in zip(segments, addresses):
        print(f"Sending message to {address}")
        server.sendto(segment.encode(FORMAT), address)
        
          
def start():
    print(f"Server listening on {HOST}:{PORT}")
    while True:
        data, address = server.recvfrom(1024)
        message = data.decode(FORMAT)
        print(f"Message from {address}: {message}")
        if message == AVAILABLE:
            addresses.append(address)
        server.sendto('Got your message'.encode(FORMAT), address) 
        
        data = input("Input Paragraph: ")
        distribute_tasks(addresses, data)
print("Server is starting...")
start()