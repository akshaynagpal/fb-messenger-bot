import watson
import nlp
from intent_guesser import IntentGuesser
from response_builder import ResponseBuilder
from basic_responder import BasicResponder
import copy

class Engine:
    def __init__(self,
                 training_data_path,
                 basic_intents_csv,
                 guess = False,
                 intent_confidence_thresh = .75):
        self.response_builder = ResponseBuilder(training_data_path)
        self.basic_responder = BasicResponder(basic_intents_csv)        
        self.intent_guesser = IntentGuesser(training_data_path)
        self.intent_thresh = intent_confidence_thresh
        self.conversation_context = {}
        self.guess = guess
        self.watson = watson.ConversationAPI(watson.rohan_graduate_affairs_config())

    def initialize_context(self, conv_id):
        if conv_id not in self.conversation_context:
            v = {'entities':set(), 'intent':None, 'response':None}
            self.conversation_context[conv_id] = v

    def clear_context(self, conv_id):
        self.conversation_context.pop(conv_id, None)
            

    def extract_entities(self, conv_id, response):
        entities = [x['entity'] for x in response['entities']]
        self.conversation_context[conv_id]['entities'].update(entities)

    def guess_intent(self, conv_id):
        intent_guess = self.intent_guesser.guess_intent(
            list(self.conversation_context[conv_id]['entities']))
        return intent_guess

    
    def extract_intent(self, conv_id, response):
        intents = [x['intent'] for x in response['intents'] if x['confidence'] > self.intent_thresh]
        if len(intents) > 0:
            self.conversation_context[conv_id]['intent'] = intents[0]

        #  if no intents from watson, try to guess using the entities
        # from the response
        else:
            entities = [x['entity'] for x in response['entities']]
            intent_guess = self.intent_guesser.guess_intent(entities)
            self.conversation_context[conv_id]['intent'] = intent_guess
            

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
            
        

    # Process message focuses on the question or intent of the message above all else. For sentences that don't express intent, it collects entities. If it doesn't find an intent but finds entities it will make it's best guess at an intent, and corresponding response. Message is self_contained if it's in an email or feedback form. For instant message, self_contained should be false. 
    def process_message(self,
                        conv_id, message,
                        clear_context=True,
                        self_contained=False):
        # This is to manage interactions like "hi!" or "hello", etc.
        basic_response = self.basic_responder.check_and_respond(message)
        if basic_response:
            return {'entities':set(),
                    'intent':basic_response[0],
                    'response':basic_response[1]}
        
        self.initialize_context(conv_id)
        sentences = nlp.get_sentences(message)
        full_watson_response = self.watson.json_response(conv_id, self.preprocess_sentence(message))
        # self.extract_entities(conv_id, watson_response)
        for sentence in sentences:
            sentence = sentence.strip()
            clean_sentence = self.preprocess_sentence(sentence)
            watson_response = self.watson.json_response(conv_id, clean_sentence)
            print watson_response
            print sentence
            if nlp.sentence_is_question(sentence.strip()):
                self.extract_entities(conv_id, watson_response)
                self.extract_intent(conv_id,watson_response)
                context = self.conversation_context[conv_id]
                intent = context['intent']
                entities = list(context['entities'])
                context['response'] = \
                                      self.response_builder.get_best_response(intent, entities)
                if not context['response']:
                    # NOTE: this order matters. we should extract entities before guessing intent and then build response
                    self.extract_entities(conv_id, full_watson_response)
                    if not intent:
                        self.extract_intent(conv_id,full_watson_response)
                    intent = context['intent']
                    entities = list(context['entities'])
                    context['response'] = \
                                          self.response_builder.get_best_response(intent, entities)

                self.clear_context(conv_id)
                return context


        # Try using the full message to build the response
        context = self.conversation_context[conv_id]
        
        if (self_contained):
            self.extract_entities(conv_id, full_watson_response)
            self.extract_intent(conv_id,full_watson_response)
            context['response'] = self.response_builder.get_best_response(
                context['intent'],
                context['entities'])

        # If we haven't yet found an intent using watson,
        # we can guess using the extracted entities. Only if self.guess is True
        if self.guess and not context['intent']:
            context['intent'] = self.guess_intent(conv_id)
            context['response'] = \
                                  self.response_builder.get_best_response(
                                      context['intent'],
                                      context['entities'])

        ret = copy.deepcopy(context)
        if clear_context:
            self.clear_context(conv_id)
        return ret
                
            
            
def read_tsv(fname):
    import csv
    l = []
    with open(fname, 'r') as f:
        tsv = csv.reader(f, delimiter='\t')
        for line in tsv:
            l.append(line)
    return l

def prompt(engine):
    from sys import stdin
    i = 0
    while True:
        print "Your message:",
        message = stdin.readline()
        result = engine.process_message(0, message, False)
        i += 1
        print result
        

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('traintsv')
    parser.add_argument('basicintentscsv')    
    args = parser.parse_args()
    data = read_tsv(args.traintsv)

    # initialize engine
    engine = Engine(args.traintsv, args.basicintentscsv)
    prompt(engine)
    # for i, line in enumerate(data):
    #     query = line[0]
    #     print "Query: ", query
    #     print engine.process_message(i, query)
        
    
  
if __name__ == "__main__":
    main()
