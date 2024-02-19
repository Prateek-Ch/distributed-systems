import socket, pickle, threading, time, queue, signal, sys, os
from bully import Node, LEADER_ID, LEADER_HOST, LEADER_PORT, ELECTION_REQUEST, OK_MESSAGE
from processing import input_batch
host = ''
port = 0
AVAILABLE = 'available'
ACK = 'ack'
RESULT_ACK = 'result_ack'
LEADER_ELECTED = 'leader_elected'
SERVER_HEARTBEAT_INTERVAL = 5 # seconds
SERVER_HEARTBEAT_TIMEOUT = 16  # seconds
last_heartbeat = {}

send_queue = queue.Queue()

server_available_event = threading.Event()
exit_flag_event = threading.Event()

send_queue_lock = threading.Lock()
client_addresses = []
nodes = []
leader = None
election_begin_time = None
ok_count = 0
address_mapping = {}

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def signal_handler(sig, frame):
    exit_flag_event.set()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def dynamic_host_discovery():
    global host, port, client_addresses, nodes, client
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
            temp = []
            for i in range(len(client_addresses)):
                chost, cport = client_addresses[i]
                address_mapping[(chost, cport)] = i
                node = Node(i, chost, cport, client)
                if node not in temp:
                    temp.append(node)
            nodes = temp
            last_heartbeat["server"] = time.time()
            server_available_event.set()

def listen_for_leader():
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
            _, current_sock_port = client.getsockname()
            current_sock_host = '192.168.0.101'
            if current_sock_host == message[LEADER_HOST] and current_sock_port == message[LEADER_PORT] and current_sock_host == message[LEADER_HOST]:
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

def leader_elected():
    while True:
        election_elapsed_time = time.time() - election_begin_time
        if leader is None and election_elapsed_time > 7 and ok_count == 0:
            _, current_sock_port = client.getsockname()
            current_sock_host = '192.168.0.101'
            leader_id = address_mapping[(current_sock_host, current_sock_port)]
            broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            broadcast_socket.sendto(pickle.dumps({LEADER_ID: leader_id, LEADER_HOST: current_sock_host, LEADER_PORT: current_sock_port}), ('192.168.0.101', 37021))
            break

# check server heartbeat
def server_heartbeat():
    global leader, election_begin_time, ok_count, nodes
    while True:
        if exit_flag_event.is_set():
            break
        time.sleep(SERVER_HEARTBEAT_INTERVAL)
        current_time = time.time()
        if current_time - last_heartbeat["server"] > SERVER_HEARTBEAT_TIMEOUT:
            print("time to elect a new leader")
            leader = None
            ok_count = 0
            if len(nodes) == 1:
                broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                broadcast_socket.sendto(pickle.dumps({LEADER_ID: nodes[0].node_id, LEADER_HOST: nodes[0].host, LEADER_PORT: nodes[0].port}), ('192.168.147.255', 37021))
            else:
                _, current_sock_port = client.getsockname()
                current_sock_host = '192.168.0.101'
                id = address_mapping[(current_sock_host, current_sock_port)]
                node = nodes[id]
                threading.Thread(target=node.start_election, args=(nodes,), daemon=True).start()
            election_begin_time = time.time()
            threading.Thread(target=listen_for_leader, daemon=True).start()
            threading.Thread(target=leader_elected, daemon=True).start()
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
        if type(data_received) == dict and ELECTION_REQUEST in data_received.keys():
            print(f"Node {data_received['target_node'].node_id} receives an election message from Node {data_received['initiating_node'].node_id}.")
            if leader is None or data_received['target_node'].node_id > leader.node_id:
                print(f"Node {data_received['target_node'].node_id} sends an OK message to Node {data_received['initiating_node'].node_id}.")
                message = {OK_MESSAGE: 'ok', 'responding_node': data_received['target_node'], 'initiating_node': data_received['initiating_node']}
                client.sendto(pickle.dumps(message), (data_received['initiating_node'].host, data_received['initiating_node'].port))
            else:
                print(f"Node {data_received['target_node'].node_id} ignores the election message from Node {data_received['initiating_node'].node_id}.")
        
        if type(data_received) == dict and OK_MESSAGE in data_received.keys():
            ok_count += 1
            leader = data_received['responding_node']
            print(f"Node {data_received['initiating_node'].node_id} acknowledges Node {data_received['responding_node'].node_id} as the leader.")    
        
        if type(data_received) == dict and 'data' in data_received.keys():
            # words = data_received['data'].split()
            # result_dict = {'id': data_received['id'], 'ngram': len(words)}
            # with send_queue_lock:
            #     print(f"Queueing: {result_dict}")
            #     send_queue.put(result_dict)

            paras = data_received['data']
            n_grams = input_batch(paras, 3)
            print(f"Ngrams {n_grams}")
            result_dict = {'id': data_received['id'], 'ngram': n_grams, 'ngram_count': len(n_grams)}
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