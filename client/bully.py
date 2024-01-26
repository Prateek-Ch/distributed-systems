import socket
import pickle
import threading

LEADER_ID = 'leader_id'
LEADER_HOST = 'leader_host'
LEADER_PORT = 'leader_port'
ELECTION_REQUEST = 'election_request'
OK_MESSAGE = 'ok_message'

class Node:
    leader_id = None
    leader_host = None
    leader_port = None
    
    def __init__(self, node_id, host, port, client):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.leader = None
        self.client = client

    def start_election(self, nodes):
        print(f"{self.node_id} initiates an election.")
        higher_nodes = [node for node in nodes if node.node_id > self.node_id]
        for higher_node in higher_nodes:
            election_message = {ELECTION_REQUEST: True, 'initiating_node': self, 'target_node': higher_node}
            self.send_message(higher_node, election_message)

    def send_message(self, target_node, message):
        print(f"{self.node_id} sends message to Node {target_node.node_id}.")
        try:
            client = message['initiating_node'].client
            message['initiating_node'].client = None
            message['target_node'].client = None
            client.sendto(pickle.dumps(message), (target_node.host, target_node.port))
        except socket.error as e:
            print(f"Error sending message to ({target_node.host}:{target_node.port}): {e}")

            
            
def elect_leader(nodes: list):
    threads = []
    if len(nodes) == 1:
        Node.leader_id = nodes[0].node_id
        Node.leader_host = nodes[0].host
        Node.leader_port = nodes[0].port
    else:
        for node in nodes:
            thread = threading.Thread(target=node.start_election, args=(nodes,), daemon=True)
            threads.append(thread)
            thread.start()
    
        # Wait for all threads to finish
        for thread in threads:
            thread.join()