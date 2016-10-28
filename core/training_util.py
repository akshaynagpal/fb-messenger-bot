import csv
from nltk.tokenize import sent_tokenize, word_tokenize
import nltk
import math

# Global
normalized_word_map = {}


def add_to_normalized_word_map(key, value):
    if key not in normalized_word_map:
        normalized_word_map[key] = set()
    normalized_word_map[key].add(value)
# Read training data into list of lists. Each sublist [question, answer, intent, entities]
def read_tsv(fname):
    l = []
    with open(fname, 'r') as f:
        tsv = csv.reader(f, delimiter='\t')
        for line in tsv:
            l.append(line)
    return l

def get_non_questions(data):
    for line in data:
        query = line[0]
        entities = line[3]
        sentences = sent_tokenize(query)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence.endswith('?'):
                if sentence.endswith('.'):
                    sentence = sentence[:-1]
                print sentence



# Taken from                 
# https://gist.github.com/alexbowe/879414
def get_nounphrases(text):
    sentence_re = r'''(?x)      # set flag to allow verbose regexps
      ([A-Z])(\.[A-Z])+\.?  # abbreviations, e.g. U.S.A.
    | \w+(-\w+)*            # words with optional internal hyphens
    | \$?\d+(\.\d+)?%?      # currency and percentages, e.g. $12.40, 82%
    | \.\.\.                # ellipsis
    | [][.,;"'?():-_`]      # these are separate tokens
    '''
    
    lemmatizer = nltk.WordNetLemmatizer()
    stemmer = nltk.stem.porter.PorterStemmer()
    
    #Taken from Su Nam Kim Paper...
    grammar = r"""
        NBAR:
            {<NN.*|JJ>*<NN.*>}  # Nouns and Adjectives, terminated with Nouns
            
        NP:
            {<NBAR>}
            {<NBAR><IN><NBAR>}  # Above, connected with in/of/etc...
    """
    chunker = nltk.RegexpParser(grammar)
    
    toks = nltk.regexp_tokenize(text, sentence_re)
    postoks = nltk.tag.pos_tag(toks)
    
    
    tree = chunker.parse(postoks)
    
    from nltk.corpus import stopwords
    stopwords = stopwords.words('english')
    

    
    def leaves(tree):
        """Finds NP (nounphrase) leaf nodes of a chunk tree."""
        for subtree in tree.subtrees(filter = lambda t: t.label()=='NP'):
            yield subtree.leaves()
    
    def normalise(word):
        """Normalises words to lowercase and stems and lemmatizes it."""
        original = word
        word = word.lower()
        word = stemmer.stem_word(word)
        word = lemmatizer.lemmatize(word)
        add_to_normalized_word_map(word, original)
        return word
    
    def acceptable_word(word):
        """Checks conditions for acceptable word: length, stopword."""
        accepted = bool(2 <= len(word) <= 40
            and word.lower() not in stopwords)
        return accepted
    
    
    def get_terms(tree):
        for leaf in leaves(tree):
            term = [ (w, normalise(w)) for w,t in leaf if acceptable_word(w) ]
            yield term
    
    terms = get_terms(tree)

    ret = []
    for term in terms:
        np = ""
        og_np = ""
        for og,word in term:
            np += word  + " "
            og_np += og + " "
        ret.append(np)
        add_to_normalized_word_map(np.strip(), og_np.strip())
    return ret
                    
def get_mapped_entities(data):
    ret = []
    for line in data:
        query = line[0]
        query = query.decode('utf-8')

        if not line[3].strip():
            continue
        entities = line[3].split(',')
        nps = get_nounphrases(query)
        for ent in entities:
            for np in nps:
                np =  np.strip()
                if not np:
                    continue
                ret.append((np, ent))
    return ret

def increment_word(d, word):
    if word not in d:
        d[word] = 0.0
    d[word] += 1.0

def compute_marginal_counts(mapped_entities):
    # Key =  word1, word2, or word1:word2
    # Value = count
    ret = {}
    for np,ent in mapped_entities:
        increment_word(ret, np)
        increment_word(ret, ent)
        increment_word(ret, np + ":" + ent)
    return ret

def compute_pmi_per_pair(marginal_counts, normalization_factor):
    ret = []
    for k,v in marginal_counts.items():
        if v < 2:
            continue
        
        if ":" in k:
            word1 = k.split(':')[0]
            word2 = k.split(':')[1]
            p_word1 = marginal_counts[word1]/normalization_factor
            p_word2 = marginal_counts[word2]/normalization_factor
            p_word1_word2 = v/normalization_factor
            pmi = math.log(p_word1_word2 / (p_word1 * p_word2)) / -(math.log(p_word1))
            ret.append([word1, word2, p_word1_word2, pmi, pmi * p_word1_word2])
    return ret
            

def print_basic_intents(data, fname):
    with open(fname, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_ALL)
        for line in data:
            intent = line[2]
            query = line[0]
            sentences = sent_tokenize(query)
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence.endswith('?'):
                    writer.writerow([sentence, intent])
                else:
                    writer.writerow([sentence, "background"])

def print_entities(scored_word_entities, outfile, threshold = 0.0):
    with open(outfile, 'wb') as f:
	for line in scored_word_entities:
	    normalized_word = line[0]
	    entity = line[1]
	    product = line[4]
	    if product <= threshold:
	        continue
	    for utterance in normalized_word_map[normalized_word]:
	        f.write( "{},{}".format(entity.encode('utf-8').strip().replace(' ', '_'), utterance) + "\n")
            

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('traintsv')
    parser.add_argument('entitiescsv')
    parser.add_argument('intentscsv')    
    args = parser.parse_args()
    

    data = read_tsv(args.traintsv)
    potential_text_entities = get_mapped_entities(data)

    normalization_factor =  len(potential_text_entities)
    pmi_scores = compute_pmi_per_pair(
        compute_marginal_counts(potential_text_entities),
        normalization_factor)

    pmi_scores.sort(key=lambda x: x[3], reverse=True)

    # print "Scored by PMI\n" + "-"*80
    # for line in pmi_scores:
    #     print line

    # pmi_scores.sort(key=lambda x: x[2], reverse=True)
    # print "Scored by p(noun phrase,entity)\n" + "-"*80
    
    # for line in pmi_scores:
    #     print line

    # pmi_scores.sort(key=lambda x: x[4], reverse=True)
    # print "Scored by product\n" + "-"*80
    
    # for line in pmi_scores:
    #     print line


    print_entities(pmi_scores, args.entitiescsv)
    

    #get_non_questions(data)
    
    print_basic_intents(data, args.intentscsv)

if __name__ == "__main__":
    main()


