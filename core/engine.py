import watson
import nlp

class Engine:
    def __init__(self,
                 entity_confidence_thresh = .5,
                 intent_confidence_thresh = .25):
        self.entity_thresh = entity_confidence_thresh
        self.intent_thresh = intent_confidence_thresh
        self.conversation_context = {}
        self.watson = watson.ConversationAPI(watson.graduate_affairs_2_config())

    def extract_entities(self, response):
        print response
        pass
    
    def extract_intent(self, response):
        pass

    def preprocess_token(self, token):
        token = nlp.strip_nonalpha_numeric(token)
        # TODO Add autocorrect. Word might be mispelled..Integrate in nlp component not here.
        return token

        
    def preprocess_sentence(self, sentence):
        tokens = nlp.tokenize_text(sentence)
        ret = ""
        for token in tokens:
            ret += self.preprocess_token(token) + " "
        return ret.strip()
            
        
        
    def process_message(self, conv_id, message):
        sentences = nlp.get_sentences(message)
        for sentence in sentences:
            sentence = self.preprocess_sentence(sentence)
            watson_response = self.watson.json_response(conv_id, sentence)
            self.extract_entities(watson_response)
            if nlp.sentence_is_question(sentence):
                self.extract_intent(watson_response)
            
            
def read_tsv(fname):
    import csv
    l = []
    with open(fname, 'r') as f:
        tsv = csv.reader(f, delimiter='\t')
        for line in tsv:
            l.append(line)
    return l

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('traintsv')
    args = parser.parse_args()
    data = read_tsv(args.traintsv)

    # initialize engine
    engine = Engine()
    
    for i, line in enumerate(data):
        query = line[0]
        engine.process_message(i, query)
        
    
  
if __name__ == "__main__":
    main()
