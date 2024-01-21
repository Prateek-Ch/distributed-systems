import socket
import pickle
import threading

LEADER_ID = 'leader_id'
ELECTION_REQUEST = 'election_request'
OK_MESSAGE = 'ok_message'

class Node:
    leader_id = None
    def __init__(self, node_id, host, port, client):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.leader = None
        self.client = client
    
    def __str__(self):
        return f"Node {self.node_id}"

    def start_election(self, nodes):
        print(f"{self} initiates an election.")
        higher_nodes = [node for node in nodes if node.node_id > self.node_id]
        for higher_node in higher_nodes:
            higher_node.receive_election(self)

    def receive_election(self, initiating_node):
        print(f"{self} receives an election message from {initiating_node}.")
        if self.leader is None or self.node_id > self.leader.node_id:
            print(f"{self} sends an OK message to {initiating_node}.")
            initiating_node.receive_ok(self)
        else:
            print(f"{self} ignores the election message from {initiating_node}.")

    def receive_ok(self, responding_node):
        print(f"{self} receives an OK message from {responding_node}.")
        self.leader = responding_node
        print(f"{self} acknowledges {responding_node} as the leader.")
        Node.leader_id = self.leader.node_id 

            
            
def elect_leader(nodes: list):
    threads = []
    for node in nodes:
        thread = threading.Thread(target=node.start_election, args=(nodes,), daemon=True)
        threads.append(thread)
        thread.start()
    
     # Wait for all threads to finish
    for thread in threads:
        thread.join()
    
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.sendto(pickle.dumps({LEADER_ID: Node.leader_id}), ('192.168.1.255', 37021))