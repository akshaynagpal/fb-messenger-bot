import csv
from nltk.tokenize import sent_tokenize, word_tokenize
import nltk
import math
import nlp
from word2vec import EmbeddingHelper



# Load Google's pre-trained Word2Vec model.
embedding_helper = EmbeddingHelper('training/question-answers-2016-11-10.vec')

# Read training data into list of lists. Each sublist [question, answer, intent, entities]
def read_tsv(fname):
    l = []
    with open(fname, 'r') as f:
        tsv = csv.reader(f, delimiter='\t')
        for line in tsv:
            l.append(line)
    return l

def filter_entities(tuples, threshold, entity):
    print tuples
    ret = []
    for word,score in tuples:
        if score > threshold:
            ret.append((word, entity))
    return ret

                    
def get_mapped_entities(data, word2vec_thresh = .3, fuzzy_thresh = 60):
    ret = set()
    potential_text_entities = []
    for line in data:
        query = line[0]
        query = query.decode('utf-8')

        if not line[3].strip():
            continue
        entities = line[3].split(',')
        nps = nlp.get_nounphrases(query, should_normalize=False)
        for ent in entities:
            simstring_results = filter_entities(process.extract(ent, nps),
                                                fuzzy_thresh,
                                                ent)
            word2vec_results =  filter_entities(embedding_helper.extract(ent, nps),
                                                word2vec_thresh,
                                                ent)
            print simstring_results
            print word2vec_results
            
            ret.update(simstring_results)
            ret.update(word2vec_results)
            if len(simstring_results) == 0 and len(word2vec_results) == 0:
                for np in nps:
                    potential_text_entities.append((np, ent))
    return list(ret), potential_text_entities


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
        # if v < 2:
        #     continue
        
        if ":" in k:
            np = k.split(':')[0]
            entity = k.split(':')[1]
            p_np = marginal_counts[np]/normalization_factor
            p_entity = marginal_counts[entity]/normalization_factor
            p_entity_np = v / normalization_factor
            p_entity_given_np = v/marginal_counts[np]
            pmi = math.log(p_entity_np / (p_np * p_entity)) / -(math.log(p_np))
            ret.append([np, entity, p_entity_np, pmi, math.sqrt(p_entity_given_np* p_entity_np)])
    return ret
            

def print_basic_intents(data, fname):
    with open(fname, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_ALL)
        for line in data:
            intent = line[2]
            if ',' in intent:
                intent = intent.split(',')[0]
            if not intent.strip():
                continue
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

def print_entities(tuples, outfile):
    with open(outfile, 'wb') as f:
        for np, entity in tuples:
            f.write("{},{}".format(entity.encode('utf-8').strip().replace(' ', '_'), np) + "\n")
        
def print_entities_score(scored_word_entities, outfile, index , threshold = 0.0):
    with open(outfile, 'a') as f:
	for line in scored_word_entities:
	    normalized_word = line[0]
	    entity = line[1]
	    prob = line[2]
            pmi = line[3]
            cond_prob = line[4]
	    if line[index] <= threshold:
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
    pretty_good_entities, potential_text_entities = get_mapped_entities(data)
    # for pair in pretty_good_entities:
    #     print pair

    # print potential_text_entities


    normalization_factor =  len(potential_text_entities)
    pmi_scores = compute_pmi_per_pair(
        compute_marginal_counts(potential_text_entities),
        normalization_factor)

    # pmi_scores.sort(key=lambda x: x[3], reverse=True)
    # pmi_scores.sort(key=lambda x: x[0])    

    # print "Scored by PMI\n" + "-"*80
    # for line in pmi_scores:
    #     print line

    # pmi_scores.sort(key=lambda x: x[2], reverse=True)
    # print "Scored by p(noun phrase,entity)\n" + "-"*80
    
    # for line in pmi_scores:
    #     print line

    pmi_scores.sort(key=lambda x: x[4], reverse=True)
    print "Scored by conditional probability of entity given np\n" + "-"*80
    
    for line in pmi_scores:
        print line


    print_entities(pretty_good_entities, args.entitiescsv)
    print_entities_score(pmi_scores,
                         args.entitiescsv,
                         4, # threshold on the conditional probability of entity
                         .075) 
    

    # #get_non_questions(data)
    
    print_basic_intents(data, args.intentscsv)

if __name__ == "__main__":
    # Run main
    main()


