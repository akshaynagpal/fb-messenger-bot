import json
import nlp
import watson
import csv

basic_grammar = {
    "cs-hello":"Hello! We hope to answer any questions you have!",
    "cs-goodbye":"Goodbye!",
    "cs-thankyou":"No problem."
}


def read_csv(fname):
    l = []
    with open(fname, 'r') as f:
        tsv = csv.reader(f, delimiter=',')
        for line in tsv:
            l.append(line)
    return l


class BasicResponder:
    def __init__(self,
                 basic_intent_csv,
                 word_threshold = 3,
                 intent_threshold = .9):
        self.intent_map = {}
        intent_utterances = read_csv(basic_intent_csv)
        for s in intent_utterances:
            self.intent_map[s[0].lower()] = s[1]
        self.response_map = basic_grammar
        self.word_threshold = word_threshold


    # Return true if message requires basic response
    def requires_basic_response(self,
                                message):
        tokens = nlp.tokenize_text(message)
        return len(tokens) <= self.word_threshold


    def produce_response(self,
                         message):
        message = message.lower()
        intent = None
        for k,v in self.intent_map.items():
            if k in message or message in k:
                intent = v
        if intent:
            if intent in self.response_map:
                return (intent, self.response_map[intent])
            return (intent, None)
        return None

    # Return None unless requires_basic_message is true and produce_response finds a match. Otherwise return a tuple with intent and response)
    def check_and_respond(self,
                           message):
        if self.requires_basic_response(message):
            return self.produce_response(message)
        return None

import unittest

class TestBasicResponder(unittest.TestCase):

    def setUp(self):
        self.br = BasicResponder('training/general-intents.csv')

    
    def test_requires(self):
        s = "the dog is running"
        self.assertFalse(self.br.requires_basic_response(s))
        s = "the dog"
        self.assertTrue(self.br.requires_basic_response(s))        

    def test_produce_response(self):
        s = "Thanks!"
        self.assertEqual("No problem.", self.br.produce_response(s)[1])
        

    
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBasicResponder)
    unittest.TextTestRunner(verbosity=2).run(suite)

    
