import socket, threading, pickle, time, uuid, queue
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
resend_queue = queue.Queue()
id_to_address = {}

# locks for race conditions
addresses_lock = threading.Lock()
last_heartbeat_lock = threading.Lock()
results_lock = threading.Lock()
resend_queue_lock = threading.Lock()
task_distributed_lock = threading.Lock()
id_to_address_lock = threading.Lock()

def distribute_tasks(addresses, data):
    global task_distributed
    segments = create_segments(data, len(addresses))
    for segment, address in zip(segments, addresses):
        unique_id = str(uuid.uuid4())
        segment_with_id = {'id': unique_id, 'data': segment}
        print(f"Sending message to {address}")
        # TODO: Implement try catch blocks after every server.send
        server.sendto(pickle.dumps(segment_with_id), address)
        segments_with_ids.append(segment_with_id)
        id_to_address[unique_id] = address
    task_distributed = True

def handle_input():
    global task_distributed
    while True:
        with task_distributed_lock:
            if len(addresses) > 0 and not task_distributed:
                data = input("Input Paragraph: ")
                distribute_tasks(addresses, data)
            
def calculate_result():
    # TODO: make this logic better
    global task_distributed
    while True:
        ids_in_segments = set(d1['id'] for d1 in segments_with_ids)
        ids_in_results = set(d2['id'] for d2 in results)
        all_keys_match = ids_in_segments == ids_in_results
        
        with task_distributed_lock:
            if task_distributed and all_keys_match and len(results) > 0:
                with results_lock:
                    result = sum(entry['ngram'] for entry in results)
                    print(f"Final result: {result}")
                    results.clear()
                    segments_with_ids.clear()
                    id_to_address.clear()
                    task_distributed = False
            with id_to_address_lock:
                id_to_address_match = all(address in addresses for address in id_to_address.values())
                if task_distributed and not id_to_address_match:
                    with results_lock:
                        for segment_with_id in segments_with_ids:
                            if not any(entry['id'] == segment_with_id['id'] for entry in results):
                                with resend_queue_lock:
                                    # Check if the id is not in the resend_queue before putting it
                                    if not any(entry['id'] == segment_with_id['id'] for entry in resend_queue.queue):
                                        resend_queue.put(segment_with_id)
                                    

def dynamic_host_discovery_and_heartbeats():
    global task_distributed, addresses, last_heartbeat
    while True:
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("sending broadcast for heartbeat and dhd")
        with addresses_lock, last_heartbeat_lock:
            broadcast_socket.sendto(pickle.dumps({'HOST': HOST, 'PORT': PORT}), ('192.168.1.255', 37020))
            
            # heartbeat
            time.sleep(HEARTBEAT_INTERVAL)
            current_time = time.time()
            # Check for client heartbeats and redistribute tasks if a client is unresponsive
            for address, last_time in list(last_heartbeat.items()):
                if current_time - last_time > HEARTBEAT_TIMEOUT:
                    print(f"Client at {address} is unresponsive.")
                    # remove from addresses list and last heartbeat
                    addresses = [x for x in addresses if x != address]
                    del last_heartbeat[address]
                    print(f"addresses list: {addresses}")
            
def resend_segments():
    global task_distributed
    while True:
        time.sleep(7)
        with task_distributed_lock:
            if task_distributed and not resend_queue.empty():
                with resend_queue_lock:
                    segment_with_id = resend_queue.get()
                    print(f"Resending segment to another available client: {segment_with_id}")
                    # make this address retrieval a bit better
                    address = addresses[0]
                    with id_to_address_lock:
                        id_to_address[segment_with_id['id']] = address
                        server.sendto(pickle.dumps(segment_with_id), address)     
                      
def start():
    global last_heartbeat
    print(f"Server listening on {HOST}:{PORT}")
    
    # TODO: figure out if starting threads like this is safe and check for race conditions
    input_thread = threading.Thread(target=handle_input, daemon= True)
    results_thread = threading.Thread(target=calculate_result, daemon=True)
    discovery_heartbeat_thread = threading.Thread(target=dynamic_host_discovery_and_heartbeats, daemon=True)
    resend_thread = threading.Thread(target=resend_segments, daemon=True)
    
    input_thread.start()
    results_thread.start()
    discovery_heartbeat_thread.start()
    resend_thread.start()
    
    while True:
        try:
            data, address = server.recvfrom(1024)
            # Process the received data
        except ConnectionResetError:
            print("ConnectionResetError: Client forcefully closed the connection")
        message = pickle.loads(data)
        server.sendto(pickle.dumps(ACK), address)
        if message == AVAILABLE:
            with addresses_lock:
                if address not in addresses:
                    addresses.append(address)
            with last_heartbeat_lock:
                last_heartbeat[address] = time.time()
        elif type(message) == dict and 'ngram' in message.keys():
            print(f"Message from {address}: {message}")
            with results_lock:   
                results.append({'id': message['id'], 'ngram': int(message['ngram'])})
print("Server is starting...")
start()