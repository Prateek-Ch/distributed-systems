import socket, pickle, threading, time, queue

host = ''
port = 0
AVAILABLE = 'available'
ACK = 'ack'
RESULT_ACK = 'result_ack'
SERVER_HEARTBEAT_INTERVAL = 5 # seconds
SERVER_HEARTBEAT_TIMEOUT = 11  # seconds
last_heartbeat = {}

send_queue = queue.Queue()
client_addresses = []

server_available_event = threading.Event()

send_queue_lock = threading.Lock()

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.setblocking(0)

def dynamic_host_discovery():
    global host, port, client_addresses
    print("waiting for server..")
    discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    discovery_socket.bind(("", 37020))

    while True:
        data, _ = discovery_socket.recvfrom(1024)
        message = pickle.loads(data)
        if 'HOST' and 'PORT' in message.keys():
            print(f"Server available at {message['HOST']}:{message['PORT']}")
            client.sendto(pickle.dumps(AVAILABLE), (message['HOST'], message['PORT']))
            host = message['HOST']
            port = message['PORT']
            client_addresses = message['ADDRESSES']
            last_heartbeat["server"] = time.time()
            server_available_event.set()

discovery_thread = threading.Thread(target=dynamic_host_discovery, daemon=True)
discovery_thread.start()

# Wait for the server discovery before proceeding
server_available_event.wait()

def send_result_message():
    while True:
        time.sleep(10)
        with send_queue_lock:
            if not send_queue.empty():
                result = send_queue.queue[0]
                print(f"Sending {result} to {(host, port)}")
                client.sendto(pickle.dumps(result), (host, port))
            
threading.Thread(target=send_result_message).start()

while True:
    time.sleep(SERVER_HEARTBEAT_INTERVAL)
    current_time = time.time()
    if current_time - last_heartbeat["server"] > SERVER_HEARTBEAT_TIMEOUT:
            print("Time to elect a new leader")
    try:
        data, _ = client.recvfrom(4096)
    except BlockingIOError:
        data = None
    if data:
        data_received = pickle.loads(data)
        # TODO: replace with logic of ngram
        if type(data_received) == dict:
            words = data_received['data'].split()
            result_dict = {'id': data_received['id'], 'ngram': len(words)}
            with send_queue_lock:
                print(f"Queueing: {result_dict}")
                send_queue.put(result_dict)
        # dequeue first element
        if data_received == RESULT_ACK:
            with send_queue_lock:
                print(f"Dequeueing: {send_queue.queue[0]}")
                send_queue.get()