from core.engine import Engine
import sys
from pprint import pprint

def read_tsv(fname):
    import csv
    l = []
    with open(fname, 'r') as f:
        tsv = csv.reader(f, delimiter='\t')
        for line in tsv:
            l.append(line)
    return l

def underscore_entities(entities_w_space):
    ret = []
    for ent in entities_w_space:
        ret.append(ent.strip().replace(' ', '_'))
    return ret

def evaluate_query(engine, query, index):
    return engine.process_message(index, query)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('traintsv')
    args = parser.parse_args()
    data = read_tsv(args.traintsv)

    
    # initialize engine
    engine = Engine(args.traintsv)

    correct_entities = 0.
    correct_intents = 0.
    correct_response = 0.

    from fuzzywuzzy import fuzz

    # Begin evaluation
    for i, line in enumerate(data):
        print "Query ", i
        query = line[0]
        response = line[1]
        intent = line[2]
        entities = underscore_entities(line[3].split(','))
        result = engine.process_message(i, query)
        pprint(line)
        pprint(result)
        if len(result['entities']) >= 1 and set(entities).issubset(result['entities']):
            correct_entities += 1
        else:
            print "Entities mismatch"
            print set(entities)
            print result['entities']
            
        if intent == result['intent']:
            correct_intents += 1
        else:
            print "Intent mismatch"
            
        if result['response'] is not None and \
           fuzz.partial_ratio(response, result['response']) > 50:
            correct_response += 1
        else:
            print "Response mismatch"
            
    print "Entity score {} Intent score {} Response score {}".format(
        correct_entities/len(data),
        correct_intents/len(data),
        correct_response/len(data))

    sys.stdout.flush()
        
        
        
    
  
if __name__ == "__main__":
    main()
