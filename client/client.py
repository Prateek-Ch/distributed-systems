import socket, pickle, threading, time, queue
from bully import Node, LEADER_ID, elect_leader
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
leader_required_event = threading.Event()
leader_elected_event = threading.Event()

send_queue_lock = threading.Lock()
client_addresses = []
nodes = []
new_leader_id = None

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.setblocking(0)

def dynamic_host_discovery():
    global host, port, client_addresses, nodes
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
        time.sleep(5)
        data, addr = election_socket.recvfrom(4096)
        message = pickle.loads(data)
        if  LEADER_ID in message.keys():
            print(f"Client {message[LEADER_ID]} is elected as the leader.")
            new_leader_id = message[LEADER_ID]
            leader_required_event.set()
            break

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
            elect_leader(nodes)
            threading.Thread(target=listen_for_leader, daemon=True).start()
            leader_required_event.wait()
    try:
        data, _ = client.recvfrom(4096)
    except BlockingIOError:
        data = None
    if data != None:
        data_received = pickle.loads(data)

        # if data_received == LEADER_ELECTED:
        #     elected_leader_id = int(client.recvfrom(4096)[0])
        #     if elected_leader_id == client_node_id:
        #         print(f"I am elected as the leader! ID: {client_node_id}")
        #         leader_elected_event.set()
        #     else:
        #         print(f"Client {elected_leader_id} is elected as the leader.")
        #         leader_elected_event.clear()

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

        if leader_elected_event.is_set():
            print("Leader elected. Performing leader tasks...")
            # figure out a way to run server.py here
            time.sleep(5)
