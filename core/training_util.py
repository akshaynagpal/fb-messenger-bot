import csv
from nltk.tokenize import sent_tokenize, word_tokenize

# Read training data into list of lists. Each sublist [question, answer, intent, entities]
def read_tsv(fname):
    l = []
    with open(fname, 'r') as f:
        tsv = csv.reader(f, delimiter='\t')
        for line in tsv:
            l.append(line)
    return l

def get_non_questions(data):
    for line in data:
        query = line[0]
        entities = line[3]
        sentences = sent_tokenize(query)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence.endswith('?'):
                print sentence + "\t" + entities

def print_basic_intents(data, fname):
    with open(fname, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_ALL)
        for line in data:
            intent = line[2]
            query = line[0]
            sentences = sent_tokenize(query)
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence.endswith('?'):
                    writer.writerow([sentence, intent])
                else:
                    writer.writerow([sentence, "background"])

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('traintsv')
    parser.add_argument('intentscsv')    
    args = parser.parse_args()

    data = read_tsv(args.traintsv)
    print_basic_intents(data, args.intentscsv)

if __name__ == "__main__":
    main()


