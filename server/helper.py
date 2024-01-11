import nltk
nltk.download('punkt')

def task_distribution(paragraph, num_nodes):
    sentences = nltk.sent_tokenize(paragraph)   
    
    segments = []
    start_index = 0
    
    sentences_per_segment = len(sentences) // num_nodes
    remainder = len(sentences) % num_nodes
    
    for i in range(num_nodes):
        end_index = start_index + sentences_per_segment + (1 if i < remainder else 0)
        segments.append(' '.join(sentences[start_index:end_index]))
        start_index = end_index
    
    return segments