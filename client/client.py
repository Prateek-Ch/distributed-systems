import socket, pickle, threading, time, queue

host = ''
port = 0
AVAILABLE = 'available'
ACK = 'ack'
RESULT_ACK = 'result_ack'
send_queue = queue.Queue()

server_available_event = threading.Event()

send_queue_lock = threading.Lock()

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def dynamic_host_discovery():
    global host, port
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
    data, _ = client.recvfrom(4096)
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