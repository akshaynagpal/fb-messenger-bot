import numpy as np
import re
from nltk.tokenize import RegexpTokenizer
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tokenize import word_tokenize
from sklearn.model_selection import cross_val_score
from sklearn.metrics import accuracy_score
from nltk.corpus import stopwords
import sys
from nltk.stem.porter import PorterStemmer
import nlp


reload(sys)
sys.setdefaultencoding('utf8')

def replace_tokens(tokens):
    ret = []
    for token in tokens:
        if nlp.is_date(token):
            token = "DATE"
        ret.append(token)
    return ret

def preprocess_text(text):
    sentences = nlp.get_sentences(text)
    processed = ""
    for sentence in sentences:
        if not nlp.sentence_is_question(sentence):
            nps = replace_tokens(nlp.get_nounphrases(sentence))
            processed += " ".join(nps) + " "
            continue
        porter_stemmer = PorterStemmer()
        stop = set(stopwords.words('english'))
        tokens = replace_tokens(word_tokenize(sentence))
        cleanup = " ".join(filter(lambda word: word.lower() not in stop, tokens))
        cleanup = cleanup.encode('ascii','ignore');
        tokens = cleanup.lower().split()
        text = text.encode('ascii', 'ignore');
        # UNCOMMENT THIS LINE TO TRY STOP WORDS
        stemmed = [porter_stemmer.stem(word.encode('ascii','ignore')) for word in tokens]
        stem_clean = " ".join(stemmed)
        processed += stem_clean + " "
    return processed

knn = KNeighborsClassifier(n_neighbors=1)
dataset=pd.read_csv('../training/question-answers-2016-11-27.shuffled.tsv',delimiter='\t')
npm=dataset.as_matrix() #numpy array
x=npm[:,0]    #sentence to classify
q=[]#np.empty(176,dtype="string")
i=0
for line in x:
    q.append(preprocess_text(line))
    i+=1
r= np.asarray(q)
y=npm[:,2]   # output token_pattern=r'\b\w+\b',
# vectorizer=CountVectorizer(ngram_range=(2,2), min_df = 0.01, max_df = 0.99)
tvectorizer=TfidfVectorizer(ngram_range=(1,2))
bigram = tvectorizer.fit_transform(r)
trainx=bigram[0:120,:]
trainy=y[0:120]
testx=bigram[120:176,:]
testy=y[120:176]
knn.fit(trainx,trainy)
print knn.score(testx,testy)
# pred = knn.predict(testx)
# print np.mean(testy == pred)
# p=knn.predict(unigram)
# scores= cross_val_score(knn, unigram, y, cv=5)
# print scores.mean()
