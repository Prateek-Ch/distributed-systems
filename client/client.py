import socket

HOST = '192.168.56.1'
PORT = 9090
HEADER = 8
FORMAT = 'utf-8'

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send(msg):
    message = msg.encode(FORMAT)  
    client.sendto(message, (HOST, PORT))
    print(client.recv(2048).decode(FORMAT))
    
send("Established connection")