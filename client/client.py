import socket
import pickle
import threading

HOST = '192.168.56.1'
PORT = 9090
AVAILABLE = 'available'
ACK = 'ack'

server_available_event = threading.Event()

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def dynamic_host_discovery():
    print("waiting for server..")
    discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    discovery_socket.bind(("", 37020))

    while True:
        data, _ = discovery_socket.recvfrom(1024)
        message = pickle.loads(data)
        if message == AVAILABLE:
            print(f"Server available at {HOST}:{PORT}")
            client.sendto(pickle.dumps(AVAILABLE), (HOST,PORT))
            server_available_event.set()

discovery_thread = threading.Thread(target=dynamic_host_discovery, daemon=True)
discovery_thread.start()

# Wait for the server discovery before proceeding
server_available_event.wait()

while True:
    data, _ = client.recvfrom(4096)
    if data:
        sentence = pickle.loads(data)
        # TODO: replace with logic of ngram
        if sentence != ACK and sentence != AVAILABLE:
            words = sentence.split()
            result_dict = {'ngram': len(words)}
            client.sendto(pickle.dumps(result_dict), (HOST, PORT))