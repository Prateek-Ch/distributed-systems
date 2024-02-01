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
        higher_nodes = [node for node in nodes if node.node_id > self.node_id]
        for higher_node in higher_nodes:
            election_message = {ELECTION_REQUEST: True, 'initiating_node': self, 'target_node': higher_node}
            self.send_message(higher_node, election_message)

    def send_message(self, higher_node, message):
        try:
            message['initiating_node'].client = None
            message['target_node'].client = None
            if self.client:
                self.client.sendto(pickle.dumps(message), (higher_node.host, higher_node.port))
        except socket.error as e:
            print(f"Error sending message to ({higher_node.host}:{higher_node.port}): {e}")
