import csv
import numpy as np

def convert_word2vec_bin2text():
    model = word2vec.Word2Vec.load_word2vec_format('/Users/rohan/Downloads/GoogleNews-vectors-negative300.bin', binary=True)
    print "loaded"
    model.save_word2vec_format('/Users/rohan/Downloads/GoogleNews-vectors-negative300.txt', binary=False)
    print "written to txt format"


# Read training data into list of lists. Each sublist [question, answer, intent, entities]
def read_tsv(fname):
    l = []
    with open(fname, 'r') as f:
        tsv = csv.reader(f, delimiter='\t')
        for line in tsv:
            l.append(line)
    return l

# Generate vocabulary from question answer data
def create_vocab(data):
    vocab = set()
    from nltk.tokenize import RegexpTokenizer

    tokenizer = RegexpTokenizer(r'\w+').tokenize
    
    for line in data:
        query = line[0]
        query = query.decode('utf-8')
        toks = tokenizer(query)

        #add vocabulary from query
        for token in toks:
            vocab.add(token)
            vocab.add(token.lower())

        if not line[3].strip():
            continue

        # add vocabulary from entities
        toks = tokenizer(line[3].strip())        
        for token in toks:
            vocab.add(token)
            vocab.add(token.lower())

    return vocab


def filter_embedding_dictionary(filename, vocab, outfile):
    from tqdm import tqdm
    d = dict()
    out = open(outfile, 'wb')
    with open(filename, 'rb') as f:
        for line in tqdm(f):
            tokens = line.split()
            word = tokens[0]
            if word in vocab:
                out.write(line)
            else:
                continue
    out.close()


def load_embedding_dictionary(filename):
    d = dict()
    len_embedding = 0
    with open(filename, 'rb') as f:
        for line in f:
            tokens = line.split()
            word = tokens[0]
            embedding = np.array(map(float, tokens[1:]))
            len_embedding = embedding.shape[0]
            d[word] = embedding
    return d, len_embedding

def cosine_similarity(v1, v2):
    if np.count_nonzero(v1) == 0 or np.count_nonzero(v2) == 0:
        return 0.0
    return v1.dot(v2)/(np.linalg.norm(v1)*np.linalg.norm(v2))


class EmbeddingHelper:
    def __init__(self, embedding_path):
        self.d,self.len_embedding = load_embedding_dictionary(embedding_path)


    def get_phrase_embedding(self, phrase):
        embedding = np.zeros(self.len_embedding)
        for word in phrase.split():
            if word in self.d:
                embedding += self.d[word]
        return embedding

    def get_similarity(self, phrase1, phrase2):
        return cosine_similarity(self.get_phrase_embedding(phrase1),
                                 self.get_phrase_embedding(phrase2))

    # Return list of tuples of word and sim score
    def extract(self, query, choices):
        return [(choice, self.get_similarity(query, choice)) for choice in choices]
            
    def get_closest(self, query, choices, threshold = .5):
        word = None
        max_sim = 0.
        for choice in choices:
            sim = self.get_similarity(query, choice)
            if  max_sim < sim and sim > threshold:
                word = choice
        return word
        

def build_vector():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("question_data")
    parser.add_argument("word_vector_text")    
    parser.add_argument("out_vector")    
    args = parser.parse_args()

    vocab = create_vocab(read_tsv(args.question_data))
    filter_embedding_dictionary(args.word_vector_text, vocab, args.out_vector)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("word_vectors")
    args = parser.parse_args()
    embeddings = EmbeddingHelper(args.word_vectors)
    print embeddings.get_closest("immunization", ["meningitis vaccination", "admissions", "MMR documents"])



    
if __name__ == "__main__":
    main()

     
