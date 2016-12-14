import requests
import json
import nlp
# CLUSTER_LINK = 'https://27c2eb5a-e17a-432c-bed7-7202a3dac75a:Pbnw4BzAxkDt@gateway.watsonplatform.net/retrieve-and-rank/api/v1/solr_clusters/sc9058a63b_6417_4dc5_ad5c_2a66cd08ee3b'
CLUSTER_LINK = 'https://42edcf2d-26f1-44e3-8887-2aad3c062b24:PNVI0DMy33zM@gateway.watsonplatform.net/retrieve-and-rank/api/v1/solr_clusters/scd080e36c_7d5b_4d53_8faa_0f59a8378b06'

def filter_links(docs):
    ret = []
    for doc in docs:

        if 'twitter' in doc['title'][0]:
            continue
        ret.append(doc)
    return ret

def query(query, fields=['id','title', 'body']):
    query = ' '.join(nlp.get_nounphrases(query, should_normalize=False))
    solr_query = CLUSTER_LINK + '/solr/example_collection/select?q=' + query + '&wt=json&fl=' + ','.join(fields)
    print solr_query
    solr_response = requests.get(solr_query)
    docs = json.loads(solr_response.text)['response']['docs']
    return filter_links(docs)




if __name__ == '__main__':
    # print watson.message(1, "hi")
    # print watson.message(1, "deadline for phd compsci")
    from pprint import pprint
    def print_results(results):
        for result in results:
            pprint(result)
            print " "

        
    # print_results(query( "I submitted uah applications (including International House) a while ago. I was wondering when the results will come out? "))
    
    print_results(query("How do I submit my immunization documentation?", fields=['title']))
#    print query( "How to transfer my I20 from another school?")[:4]
