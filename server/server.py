import socket, threading, pickle
from helper import create_segments

HOST = socket.gethostbyname(socket.gethostname())
PORT = 9090
AVAILABLE = 'available'
ACK = 'ack'

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))

addresses = []
results = []

def distribute_tasks(addresses, data):
    segments = create_segments(data, len(addresses))
    for segment, address in zip(segments, addresses):
        print(f"Sending message to {address}")
        server.sendto(pickle.dumps(segment), address)

def handle_input():
    while True:
        if len(addresses) > 0:
            data = input("Input Paragraph: ")
            distribute_tasks(addresses, data)
            
def calculate_result():
    # TODO: make this logic better
    while True:
        if len(results) == len(addresses) and len(results) > 0:
            result = sum(results)
            print(f"Final result: {result}")
            results.clear()
            
          
def start():
    print(f"Server listening on {HOST}:{PORT}")
    # TODO: figure out if starting threads like this is safe and check for race conditions
    input_thread = threading.Thread(target=handle_input, daemon= True)
    results_thread = threading.Thread(target=calculate_result, daemon=True)
    input_thread.start()
    results_thread.start()
    
    while True:
        data, address = server.recvfrom(1024)
        message = pickle.loads(data)
        print(f"Message from {address}: {message}")
        server.sendto(pickle.dumps(ACK), address)
        if message == AVAILABLE:
            addresses.append(address)
        elif type(message) == dict and 'ngram' in message.keys():
            results.append(int(message['ngram'])) 
print("Server is starting...")
start()