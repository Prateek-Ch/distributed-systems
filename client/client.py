import socket, pickle, threading, time, queue, signal, sys, os
from bully import Node, LEADER_ID, LEADER_HOST, LEADER_PORT, elect_leader
host = ''
port = 0
AVAILABLE = 'available'
ACK = 'ack'
RESULT_ACK = 'result_ack'
LEADER_ELECTED = 'leader_elected'
SERVER_HEARTBEAT_INTERVAL = 5 # seconds
SERVER_HEARTBEAT_TIMEOUT = 11  # seconds
last_heartbeat = {}

send_queue = queue.Queue()

server_available_event = threading.Event()
exit_flag_event = threading.Event()

send_queue_lock = threading.Lock()
client_addresses = []
nodes = []
new_leader_id = None

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def signal_handler(sig, frame):
    exit_flag_event.set()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def dynamic_host_discovery():
    global host, port, client_addresses, nodes
    print("waiting for server..")
    discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    discovery_socket.bind(("", 37020))

    while True:
        if exit_flag_event.is_set():
            discovery_socket.close()
            if client:
                client.close()
            break
        data, _ = discovery_socket.recvfrom(1024)
        message = pickle.loads(data)
        if 'HOST' and 'PORT' in message.keys():
            print(f"Server available at {message['HOST']}:{message['PORT']}")
            client.sendto(pickle.dumps(AVAILABLE), (message['HOST'], message['PORT']))
            host = message['HOST']
            port = message['PORT']
            client_addresses = message['ADDRESSES']
            nodes = []
            for i in range(len(client_addresses)):
                chost, cport = client_addresses[i]
                node = Node(i, chost, cport, client)
                if node not in nodes:
                    nodes.append(node)
            last_heartbeat["server"] = time.time()
            server_available_event.set()

def listen_for_leader():
    global new_leader_id
    election_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    election_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    election_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    election_socket.bind(("", 37021))
        
    while True:
        if exit_flag_event.is_set():
            election_socket.close()
            break
        data, addr = election_socket.recvfrom(4096)
        message = pickle.loads(data)
        if  LEADER_ID in message.keys():
            print(f"Client {message[LEADER_ID]} is elected as the leader.")
            new_leader_id = message[LEADER_ID]
            _, current_sock_port = client.getsockname()
            current_sock_host = socket.gethostbyname(socket.gethostname())
            if current_sock_host == message[LEADER_HOST] and current_sock_port == message[LEADER_PORT]:
                last_heartbeat["server"] = time.time()
                print("Leader elected. Performing leader tasks...")
                print("-------RUNNING server.py HERE----------")
                current_script_dir = os.path.dirname(os.path.abspath(__file__))
                server_py = os.path.abspath(os.path.join(current_script_dir, '..', 'server/server.py')) 
                os.execv(sys.executable, ['python'] + ['"' + server_py +'"'])
            break

discovery_thread = threading.Thread(target=dynamic_host_discovery, daemon=True)
discovery_thread.start()

# Wait for the server discovery before proceeding
server_available_event.wait()

def send_result_message():
    while True:
        if exit_flag_event.is_set():
            if client:
                client.close()
            break
        time.sleep(10)
        with send_queue_lock:
            if not send_queue.empty():
                result = send_queue.queue[0]
                print(f"Sending {result} to {(host, port)}")
                client.sendto(pickle.dumps(result), (host, port))
            
threading.Thread(target=send_result_message).start()

# check server heartbeat
def server_heartbeat():
    while True:
        if exit_flag_event.is_set():
            break
        time.sleep(SERVER_HEARTBEAT_INTERVAL)
        current_time = time.time()
        if current_time - last_heartbeat["server"] > SERVER_HEARTBEAT_TIMEOUT:
            print("time to elect a new leader")
            elect_leader(nodes)
            threading.Thread(target=listen_for_leader, daemon=True).start()
            time.sleep(10)
            
threading.Thread(target=server_heartbeat, daemon=True).start()

while True:
    if exit_flag_event.is_set():
        break
    try:
        data, _ = client.recvfrom(4096)
    except BlockingIOError:
        data = None
    if data != None:
        data_received = pickle.loads(data)

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

# graceful shutdown
if client:
    client.close()
print("graceful shutdown")
sys.exit()