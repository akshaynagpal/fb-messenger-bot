import csv
from nltk.tokenize import sent_tokenize, word_tokenize
import nltk
import math
import nlp

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


                    
def get_mapped_entities(data):
    ret = []
    for line in data:
        query = line[0]
        query = query.decode('utf-8')

        if not line[3].strip():
            continue
        entities = line[3].split(',')
        nps = nlp.get_nounphrases(query)
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
            try: 
                sentences = sent_tokenize(query)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if nlp.sentence_is_question(sentence):
                        writer.writerow([sentence, intent])
                    else:
                        writer.writerow([sentence, "background"])
            except UnicodeDecodeError:
                print "Error parsing:", query
                continue

def print_entities(scored_word_entities, outfile, threshold = 0.0):
    with open(outfile, 'wb') as f:
	for line in scored_word_entities:
	    normalized_word = line[0]
	    entity = line[1]
	    pmi = line[3]
	    if pmi <= threshold:
	        continue
	    for utterance in nlp.normalized_word_map[normalized_word]:
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


    print_entities(pmi_scores, args.entitiescsv, .022)
    

    #get_non_questions(data)
    
    print_basic_intents(data, args.intentscsv)

if __name__ == "__main__":
    # Run main
    main()


