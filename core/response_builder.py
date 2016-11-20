import nlp
from fuzzywuzzy import fuzz
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

def add_to_response_dict(d,key, response):
    if key not in d:
        d[key] = {response:1}
    else:
        foundExisting = False
        for resp in d[key].keys():
            if fuzz.partial_ratio(resp, response) > 50:
                if len(response) < len(resp): # Prefer shortest response
                    freq = d[key].pop(resp, None)
                    d[key][response] = freq + 1
                else:
                    d[key][resp] += 1
                foundExisting = True

        if not foundExisting:
            d[key][response] = 1

class ResponseBuilder:
    def __init__(self,
                 training_data_path):
        data = read_tsv(training_data_path)
        self.response_dict = dict()
        for line in data:
            query = line[0]
            response = line[1]
            intent = line[2]
            entities = underscore_entities(line[3].split(','))
            key = self.build_key(intent, entities)
            add_to_response_dict(self.response_dict, key, response)

    def build_error_response():
        return "I'm sorry. We do not know how to answer your question at this point. Please email graduateaffairs@columbia.edu"
    
    # Assumes intent exists
    def build_key(self, intent, entities):
        l = list(set(entities))
        l.insert(0, intent)
        return tuple(l)

    def get_best_response(self, intent, entities):
        if len(entities) == 0 or intent is None:
            return None
        key = self.build_key(intent, entities)
        if key in self.response_dict:
            return max(self.response_dict[key].iteritems(), key=operator.itemgetter(1))[0]
        for entity in entities:
            new_entities = [ent for ent in entities if ent != entity]
            # Recurse with one less entity
            response = self.get_best_response(intent, new_entities)
            if response:
                return response
        return None
            
                
        


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('traintsv')
    args = parser.parse_args()
    data = read_tsv(args.traintsv)
    resp = ResponseBuilder(args.traintsv)
    intent = "Issue"
    entities = ["Uni", "Alias"]
    print resp.get_best_response(intent, entities)
    intent = "Notification"
    entities = ['Registration', 'UAH', 'Uni']
    print resp.get_best_response(intent, entities)


        
    
  
if __name__ == "__main__":
    main()

