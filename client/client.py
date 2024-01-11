import socket

HOST = '192.168.56.1'
PORT = 9090
HEADER = 8
FORMAT = 'utf-8'
AVAILABLE = 'available'

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.sendto(AVAILABLE.encode(FORMAT), (HOST,PORT))

while True:
    data, _ = client.recvfrom(4096) 
    print(data.decode(FORMAT))