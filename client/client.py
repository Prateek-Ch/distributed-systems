import socket, pickle

HOST = '192.168.56.1'
PORT = 9090
AVAILABLE = 'available'
ACK = 'ack'

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.sendto(pickle.dumps(AVAILABLE), (HOST,PORT))

while True:
    data, _ = client.recvfrom(4096) 
    sentence = pickle.loads(data)
    print(sentence)
    # TODO: replace with logic of ngram
    if sentence != ACK and sentence != AVAILABLE:
        words = sentence.split()
        result_dict = {'ngram': len(words)}
        client.sendto(pickle.dumps(result_dict), (HOST,PORT))