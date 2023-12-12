from nltk.util import ngrams


def find_ngrams(para, n):
    words = para.split()
    grams = ngrams(words, 2)
    grams = [" ".join(list(i)) for i in grams]
    return grams


def input_batch(paras, n):
    batch_ngrams = []
    for para in paras:
        batch_ngrams += find_ngrams(para, n)
    return input_batch
