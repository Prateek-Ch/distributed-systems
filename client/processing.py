from nltk.util import ngrams

def input_batch(paras, n):
    # Split the sentence into words
    words = paras.split()

    # Initialize an empty list to store the n-grams
    ngrams = []

    # Generate the n-grams
    for i in range(len(words) - n + 1):
        ngram = ' '.join(words[i:i + n])
        ngrams.append(ngram)

    return ngrams
