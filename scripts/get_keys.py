import csv

def read_tsv(fname):

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
    parser.add_argument('outtsv')    
    args = parser.parse_args()
    data = read_tsv(args.traintsv)
    from core.response_builder import ResponseBuilder
    rp = ResponseBuilder(args.traintsv)

    key_cache = set()
    out = open(args.outtsv, 'w')
    writer = csv.writer(out, delimiter='\t')
    for line in data:
        question = line[0]
        response = line[1]
        intent = line[2]
        original_ents = line[3]
        entities = line[3].strip().split(',')
        key = rp.build_key(intent, entities)
        if key not in key_cache:
            key_cache.add(key)
            writer.writerow([intent, original_ents, question, response])
    out.close()
        


if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    main()
            
