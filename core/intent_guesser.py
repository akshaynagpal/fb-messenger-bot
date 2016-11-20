import operator


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

def add_to_intent_dict(d,key, intent):
    if key not in d:
        d[key] = {intent:1}
    else:
        foundExisting = False
        if intent in d[key]:
            d[key][intent] += 1
        else:
            d[key][intent] = 1
        
class IntentGuesser:
    def __init__(self,
                 training_data_path):
        data = read_tsv(training_data_path)
        self.intent_dict = dict()
        for line in data:
            query = line[0]
            response = line[1]
            intent = line[2]
            entities = underscore_entities(line[3].split(','))
            key = self.build_key(entities)
            add_to_intent_dict(self.intent_dict, key, intent)

    # Assumes intent exists
    def build_key(self, entities):
        l = list(set(entities))
        return tuple(l)

    def guess_intent(self, ents):
        potential_intents = {}
        cache = set()
        def helper(entities):
            if len(entities) == 0:
                return
        
            key = self.build_key(entities)
            # Shouldn't try out same key twice
            if key in cache:
                return
            
            cache.add(key)
            if key in self.intent_dict:
                max_intent_freq = max(self.intent_dict[key].iteritems(), key=operator.itemgetter(1))
                intent = max_intent_freq[0]
                freq = max_intent_freq[1]
                if intent not in potential_intents:
                    potential_intents[intent] = freq
                else:
                    potential_intents[intent] += freq

            for entity in entities:
                new_entities = [ent for ent in entities if ent != entity]
                # Recurse with one less entity
                helper(new_entities)
                
        helper(ents)
        if len(potential_intents) == 0:
            return None
        print potential_intents
        
        most_likely_intent = max(potential_intents.iteritems(), key=operator.itemgetter(1))[0]
        return most_likely_intent


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('traintsv')
    args = parser.parse_args()
    data = read_tsv(args.traintsv)
    resp = IntentGuesser(args.traintsv)
    intent = "Issue"
    entities = ["Uni", "Alias"]
    print resp.guess_intent(entities)
    intent = "Notification"
    entities = ["Housing", "UAH", "facebook", "sys-number"]
    print resp.guess_intent(entities)


        
    
  
if __name__ == "__main__":
    main()
