import nltk
nltk.download('punkt')

def create_segments(paragraph: str, num_nodes: int):
    sentences = nltk.sent_tokenize(paragraph)   
    
    segments = []
    start_index = 0

# else added to handle num_nodes = 0
    if num_nodes > 0:
        sentences_per_segment = len(sentences) // num_nodes
        remainder = len(sentences) % num_nodes
    
        for i in range(num_nodes):
            end_index = start_index + sentences_per_segment + (1 if i < remainder else 0)
            segments.append(' '.join(sentences[start_index:end_index]))
            start_index = end_index
    
        return segments

    else:
        print(f"No Clients Found!")
        return segments