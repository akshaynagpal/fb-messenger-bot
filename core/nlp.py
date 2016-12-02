import nltk
nltk.data.path.append('./nltk_data/')
from nltk.tokenize import sent_tokenize, word_tokenize
import re, string
from dateutil.parser import parse

# consts
question_key_phrases = ["when", "how", "where", "what", "wondering", "could you", "can you"]

# Global
normalized_word_map = {}

pattern = re.compile('[\W_]+')

def is_date(string):
    try: 
        parse(string)
        return True
    except ValueError:
        return False

# Return sentences for some text
def get_sentences(text):
    sentences = None
    try:
        sentences = sent_tokenize(text)
    except UnicodeDecodeError :
        sentences = text.split('.') # Super basic sentence splitting
        print "Trouble parsing: " + text
    return sentences
        

def strip_nonalpha_numeric(word):
    return re.sub(pattern, '', word)


def add_to_normalized_word_map(key, value):
    if key not in normalized_word_map:
        normalized_word_map[key] = set()
    normalized_word_map[key].add(value)


def tokenize_text(text):
    sentence_re = r'''(?x)      # set flag to allow verbose regexps
      ([A-Z])(\.[A-Z])+\.?  # abbreviations, e.g. U.S.A.
    | \w+([-']\w+)*            # words with optional internal hyphens
    | \$?\d+(\.\d+)?%?      # currency and percentages, e.g. $12.40, 82%
    | \.\.\.                # ellipsis
    | [][.,;"'?():-_`]      # these are separate tokens
    '''

    try:
        return nltk.regexp_tokenize(text, sentence_re)
    except:
        return nltk.word_tokenize(text)

# assumes sentence is stripped of trailing white space 
def sentence_is_question(sentence):
    if sentence.endswith("?"):
        return True

    for key_word in question_key_phrases:
        key_word = key_word + " "
        if key_word in sentence.lower():
            return True
            
    return False

# Taken from                 
# https://gist.github.com/alexbowe/879414
def get_nounphrases(text, should_normalize=True):

    
    lemmatizer = nltk.WordNetLemmatizer()
    stemmer = nltk.stem.porter.PorterStemmer()
    
    #Taken from Su Nam Kim Paper...
    grammar = r"""
        NBAR:
            {<NN.*|JJ>*<NN.*>}  # Nouns and Adjectives, terminated with Nouns
            
        NP:
            {<NBAR>}
            {<NBAR><IN><NBAR>}  # Above, connected with in/of/etc...
    """
    chunker = nltk.RegexpParser(grammar)
    
    toks = tokenize_text(text)
    postoks = []
    try:
        postoks = nltk.tag.pos_tag(toks)
    except:
        return []
    
    
    tree = chunker.parse(postoks)
    
    from nltk.corpus import stopwords
    stopwords = stopwords.words('english')
    

    
    def leaves(tree):
        """Finds NP (nounphrase) leaf nodes of a chunk tree."""
        for subtree in tree.subtrees(filter = lambda t: t.label()=='NP'):
            yield subtree.leaves()
    
    def normalise(word, should_normalize):
        if not should_normalize:
            return word
        """Normalises words to lowercase and stems and lemmatizes it."""
        original = word
        word = word.lower()
        word = stemmer.stem_word(word)
        word = lemmatizer.lemmatize(word)
        add_to_normalized_word_map(word, original)
        return word
    
    def acceptable_word(word):
        """Checks conditions for acceptable word: length, stopword."""
        accepted = bool(2 <= len(word) <= 40
            and word.lower() not in stopwords)
        return accepted
    
    
    def get_terms(tree):
        for leaf in leaves(tree):
            term = [ (w, normalise(w, should_normalize)) for w,t in leaf if acceptable_word(w) ]
            yield term
    
    terms = get_terms(tree)

    ret = []
    for term in terms:
        np = ""
        og_np = ""
        for og,word in term:
            np += word  + " "
            og_np += og + " "
        ret.append(np.strip())
        add_to_normalized_word_map(np.strip(), og_np.strip())
    return ret


import unittest

class TestEntityExtraction(unittest.TestCase):

    def test_tokenization(self):
        s = "the dog is running"
        toks = tokenize_text(s)
        self.assertEqual(4, len(toks))

        s = "What to do if I forgot my I-20/DS-2019?"
        toks = tokenize_text(s)
        self.assertEqual(10, len(toks))
        self.assertEqual("I-20",toks[7])
        self.assertEqual("DS-2019",toks[8])

        s = "I was wondering when I'll be notified"
        toks = tokenize_text(s)
        self.assertEqual(7, len(toks))
        self.assertEqual("I'll",toks[4])

        
    def test_nounphrase(self):
        s = "I have some issues about my I20 and the orientation attendance"
        nps = get_nounphrases(s, False) #Don't normalize words
        self.assertEqual(3, len(nps))
        self.assertEqual("I20", nps[1])
        self.assertEqual("orientation attendance", nps[2])

        s = "I was admitted last week, but I have not yet received my student account"
        nps = get_nounphrases(s, False)
        self.assertEqual(2, len(nps))
        self.assertEqual("last week", nps[0])
        self.assertEqual("student account", nps[1])

        s = "I made a very serious mistake with my housing application offers."
        nps = get_nounphrases(s, False)
        self.assertEqual(2, len(nps))
        self.assertEqual("serious mistake", nps[0])
        self.assertEqual("housing application offers", nps[1])
        

    def test_questions(self):
        s = "I have a question about housing"
        self.assertFalse(sentence_is_question(s))

        s = "do you know when I'll receive notification of my application?"
        self.assertTrue(sentence_is_question(s))

        s = "I just wanted to know when will my application approximately be processed."
        self.assertTrue(sentence_is_question(s))

    def test_strip_nonalphanumeric(self):
        self.assertEqual("I20", strip_nonalpha_numeric("I20"))
        self.assertEqual("USA", strip_nonalpha_numeric("U.S.A"))        



if __name__ == "__main__":

    # Run units tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEntityExtraction)
    unittest.TextTestRunner(verbosity=2).run(suite)

