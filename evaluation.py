from core.engine import Engine

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

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('traintsv')
    args = parser.parse_args()
    data = read_tsv(args.traintsv)

    # initialize engine
    engine = Engine()
    correct_entities = 0.
    correct_intents = 0.

    # Begin evaluation
    for i, line in enumerate(data):
        query = line[0]
        intent = line[2]
        entities = underscore_entities(line[3].split(','))
        result = engine.process_message(i, query)
        if set(entities).issubset(result['entities']):
            correct_entities += 1
        if intent == result['intent']:
            correct_intents += 1
    print "Entity score {} Intent score {}".format(correct_entities/len(data),
                                                   correct_intents/len(data))
        
        
        
    
  
if __name__ == "__main__":
    main()