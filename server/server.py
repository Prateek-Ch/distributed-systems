import socket, threading, pickle, time, uuid
from helper import create_segments

HOST = socket.gethostbyname(socket.gethostname())
PORT = 9090
AVAILABLE = 'available'
ACK = 'ack'

HEARTBEAT_INTERVAL = 5 # seconds
HEARTBEAT_TIMEOUT = 11  # seconds
last_heartbeat = {}

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))

addresses = []
segments_with_ids = []
results = []
task_distributed = False

def distribute_tasks(addresses, data):
    global task_distributed
    segments = create_segments(data, len(addresses))
    for segment, address in zip(segments, addresses):
        unique_id = str(uuid.uuid4())
        segment_with_id = {'id': unique_id, 'data': segment}
        print(f"Sending message to {address}")
        server.sendto(pickle.dumps(segment_with_id), address)
        segments_with_ids.append(segment_with_id)
    task_distributed = True

def handle_input():
    global task_distributed
    while True:
        if len(addresses) > 0 and not task_distributed:
            data = input("Input Paragraph: ")
            distribute_tasks(addresses, data)
            
def calculate_result():
    # TODO: make this logic better
    global task_distributed
    while True:
        all_keys_match = all(d1['id'] == d2['id'] for d1, d2 in zip(segments_with_ids, results))
        if task_distributed and all_keys_match and len(results) > 0:
            result = sum(entry['ngram'] for entry in results)
            print(f"Final result: {result}")
            results.clear()
            segments_with_ids.clear()
            task_distributed = False

def dynamic_host_discovery_and_heartbeats():
    global task_distributed, addresses, last_heartbeat
    while True:
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("sending broadcast for heartbeat and dhd")
        broadcast_socket.sendto(pickle.dumps({'HOST': HOST, 'PORT': PORT}), ('192.168.1.255', 37020))
        
        # heartbeat
        time.sleep(HEARTBEAT_INTERVAL)
        current_time = time.time()
        # Check for client heartbeats and redistribute tasks if a client is unresponsive
        for address, last_time in last_heartbeat.items():
            if current_time - last_time > HEARTBEAT_TIMEOUT:
                print(f"Client at {address} is unresponsive.")
                # remove from addresses list
                addresses = [x for x in addresses if x != address]
                print(f"addresses list: {addresses}")
                task_distributed = False
            print(f"adddreses list: {addresses}")       
            
          
def start():
    global last_heartbeat
    print(f"Server listening on {HOST}:{PORT}")
    # TODO: figure out if starting threads like this is safe and check for race conditions
    input_thread = threading.Thread(target=handle_input, daemon= True)
    results_thread = threading.Thread(target=calculate_result, daemon=True)
    discovery_heartbeat_thread = threading.Thread(target=dynamic_host_discovery_and_heartbeats, daemon=True)
    
    input_thread.start()
    results_thread.start()
    discovery_heartbeat_thread.start()
    
    while True:
        data, address = server.recvfrom(1024)
        message = pickle.loads(data)
        print(f"Message from {address}: {message}")
        server.sendto(pickle.dumps(ACK), address)
        if message == AVAILABLE:
            if address not in addresses:
                addresses.append(address)
            last_heartbeat[address] = time.time()
        elif type(message) == dict and 'ngram' in message.keys():
            results.append({'id': message['id'], 'ngram': int(message['ngram'])}) 
print("Server is starting...")
start()