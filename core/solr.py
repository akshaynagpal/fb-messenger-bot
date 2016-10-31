import requests
import json

def query(query):
    solr_response = requests.get('https://27c2eb5a-e17a-432c-bed7-7202a3dac75a:Pbnw4BzAxkDt@gateway.watsonplatform.net/retrieve-and-rank/api/v1/solr_clusters/sc9058a63b_6417_4dc5_ad5c_2a66cd08ee3b/solr/example_collection/select?q=' + query + '?&wt=json&fl=body')
    return json.loads(solr_response.text)['response']['docs']
