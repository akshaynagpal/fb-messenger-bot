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
            if not response.strip():
                continue
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

    def get_best_response(self, intent_, entities_):
        cache = set()
        potential_responses = {}
        def helper(intent, entities):
            if len(entities) == 0 or intent is None:
                return None
            key = self.build_key(intent, entities)
            if key in cache:
                return
            cache.add(key)
            if key in self.response_dict:
                response = max(self.response_dict[key].iteritems(),
                                   key=operator.itemgetter(1))
                freq = response[1]
                key_dim = len(key)
                if response[0] in potential_responses:
                    val = potential_responses[response[0]]
                    freq += val[0]
                    key_dim = max(key_dim, val[1])

                potential_responses[response[0]] = (freq, key_dim)

                
            for entity in entities:
                new_entities = [ent for ent in entities if ent != entity]
                # Recurse with one less entity
                helper(intent, new_entities)
        helper(intent_, entities_)
        if len(potential_responses) == 0:
            return None

        response_list = []
        for k,v in potential_responses.items():
            row = []
            row.append(k)
            row.extend(list(v))
            response_list.append(row)

        # sort by freq and then by dimension
        response_list.sort(key=lambda x: x[1], reverse=True)
        response_list.sort(key=lambda x: x[2], reverse=True)
        print response_list
        return response_list[0][0]
        
        
            
                
        


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

