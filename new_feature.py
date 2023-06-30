import requests
from ratelimit import limits,sleep_and_retry
import json
import os
import copy
from tqdm import tqdm
import argparse
import time

# [DO NOT DELETE]get_pageid is not used by now
@limits(calls=50, period=1)# Set the rate limit to 50 requests per second
def get_pageid(pagename:str,headers:dict)->int:
    """
    read pagename and return pageid
    """
    pageid_link = 'https://en.wikipedia.org/w/rest.php/v1/page/' + pagename
    response = requests.get(pageid_link, headers=headers)
    if response.status_code == 200:# Check if the request was successful
        data = response.json()
        pageid = data['id']
    else:
        print("Request id failed with status code:", response.status_code)
    return pageid

# [DO NOT DELETE]get_pageid is not used by now
@limits(calls=50, period=1)# Set the rate limit to 50 requests per second
def get_uri(pagename:str,pageid:int,headers:dict)->str:
    """
    read pagename and pageid, return uri
    """
    uri_link = 'https://en.wikipedia.org/w/api.php?action=query&prop=pageprops&titles=' + pagename + '&format=json'
    response = requests.get(uri_link, headers=headers)
    if response.status_code == 200:# Check if the request was successful
        data = response.json()
        uri = data['query']['pages'][str(pageid)]['pageprops']['wikibase_item']
    else:
        print("Request uri failed with status code:", response.status_code)
    return uri

@limits(calls=50, period=1)# Set the rate limit to 50 requests per second
def get_pagename(uri:str,headers:dict)->str:# some uri return blank title
    """
    read uri and return pagename
    """
    pagename_link = 'https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=sitelinks&ids=' + uri + '&sitefilter=enwiki'
    response = requests.get(pagename_link, headers=headers)# Make a GET request to the API
    if response.status_code == 200:# Check if the request was successful
        data = response.json()# If the request was successful, parse the JSON data
        try:
            pagename = data['entities'][uri]['sitelinks']['enwiki']['title']# Access the pageviews data
        except KeyError:
            pagename = 'NULL'
    else:
        print("Request pagename failed with status code:", response.status_code)# If the request was not successful, print an error message
        pagename = 'NULL'
    return pagename

@limits(calls=50, period=1)# Set the rate limit to 50 requests per second
def get_pageviews_data(pagename:str,headers:dict)->list:# 0 assign used Amsterdam term
    """
    read a str pagename and dict header and return a list
    """
    url = 'https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/all-access/all-agents/' + pagename + '/monthly/2022080100/2023013100'# half year period
    response = requests.get(url, headers=headers)
    if response.status_code == 200:# Check if the request was successful
        if pagename == 'NULL':
            pageviews = [{"project":"en.wikipedia","article":"Amsterdam","granularity":"monthly","timestamp":"2022080100","access":"all-access","agent":"all-agents","views":0},{"project":"en.    wikipedia","article":"Amsterdam","granularity":"monthly","timestamp":"2022090100","access":"all-access","agent":"all-agents","views":0},{"project":"en.wikipedia","article":"Amsterdam","granularity":"monthly","timestamp":"2022100100","access":"all-access","agent":"all-agents","views":0},{"project":"en.wikipedia","article":"Amsterdam","granularity":"monthly","timestamp":"2022110100","access":"all-access","agent":"all-agents","views":0},{"project":"en.wikipedia","article":"Amsterdam","granularity":"monthly","timestamp":"2022120100","access":"all-access","agent":"all-agents","views":0},{"project":"en.wikipedia","article":"Amsterdam","granularity":"monthly","timestamp":"2023010100","access":"all-access","agent":"all-agents","views":0}]# add 0 to noname pages
        else:
            data = response.json()
            pageviews = data["items"]
    else:
        print("Request pageview failed with status code:", response.status_code)
        pageviews = [{"project":"en.wikipedia","article":"Amsterdam","granularity":"monthly","timestamp":"2022080100","access":"all-access","agent":"all-agents","views":0},{"project":"en.    wikipedia","article":"Amsterdam","granularity":"monthly","timestamp":"2022090100","access":"all-access","agent":"all-agents","views":0},{"project":"en.wikipedia","article":"Amsterdam","granularity":"monthly","timestamp":"2022100100","access":"all-access","agent":"all-agents","views":0},{"project":"en.wikipedia","article":"Amsterdam","granularity":"monthly","timestamp":"2022110100","access":"all-access","agent":"all-agents","views":0},{"project":"en.wikipedia","article":"Amsterdam","granularity":"monthly","timestamp":"2022120100","access":"all-access","agent":"all-agents","views":0},{"project":"en.wikipedia","article":"Amsterdam","granularity":"monthly","timestamp":"2023010100","access":"all-access","agent":"all-agents","views":0}]# add 0 to 404 pages
    return pageviews

@limits(calls=50, period=1)# Set the rate limit to 50 requests per second
def get_instance_of(uri:str)->str:
    '''
    give a uri and get the uri of instance of 
    '''
    # Define the Wikidata API URL
    url = "https://www.wikidata.org/w/api.php"

    # Define the item ID for the item you are interested in
    item_id = uri

    # Define the Wikidata property ID for "instance of"
    property_id = "P31"

    # Define the API parameters
    params = {
        "action": "wbgetentities",
        "ids": item_id,
        "props": "claims",
        "languages": "en",
        "format": "json"
    }

    # Make the API request
    response = requests.get(url, params=params)

    # Parse the JSON response
    if response.status_code == 200:
        data = response.json()
        # Get the "instance of" claims
        try:
            instance_of_claims = data["entities"][item_id]["claims"][property_id]
            instance_of_values = []
            for claim in instance_of_claims:
                value = claim["mainsnak"]["datavalue"]["value"]["id"]
                instance_of_values.append(value)
            #instance_of_value = instance_of_claims[0]["mainsnak"]["datavalue"]["value"]["id"]
        except KeyError:
            print("This item does not have any 'instance of' statements.")
            instance_of_values = 'NULL'
    else:
        print("Request instance uri failed with status code:", response.status_code)
        instance_of_values = 'NULL'
    return instance_of_values

# Function to retrieve the depth of a given class ID
@sleep_and_retry
@limits(calls=50, period=60)# Set the rate limit to 50 requests per second #60 seconds of processing time each 60 seconds
def get_class_depth(class_id,headers):
    # Wikidata SPARQL endpoint URL
    sparql_endpoint = "https://query.wikidata.org/sparql"
    # SPARQL query to get the depth of a class
    query = f"""
    SELECT (COUNT(?mid) AS ?depth) WHERE {{
    wd:{class_id} wdt:P279* ?mid .
    ?mid wdt:P279+ ?root .
    FILTER NOT EXISTS {{ ?root wdt:P279 ?mid . }}
    }}
    GROUP BY ?mid
    ORDER BY DESC(?depth)
    LIMIT 1
    """
    # Send a request to the SPARQL endpoint with the query
    response = requests.get(sparql_endpoint, params={"query": query, "format": "json"},headers=headers)
    # Parse the JSON response
    if response.status_code == 200:
        data = response.json()
        #print(data)
        # Extract the depth value from the response
        try:
            depth = int(data["results"]["bindings"][0]["depth"]["value"])#异常处理：可能是{'head': {'vars': ['depth']}, 'results': {'bindings': []}}
        except IndexError:
            print("No depth value.")
            depth = 99999
    else:
        print("Request sparql failed with status code:", response.status_code)
        depth = 99999
    return depth

def get_class(instance_of_values,headers)->str:
    # Dictionary to store depths for each input class
    depths_dict = {}
    # Iterate through input classes and populate the depths_dict
    if instance_of_values == 'NULL':
        coarsest_class = 'NULL'
    else:
        for class_id in instance_of_values:#["Q515", "Q1549591", "Q17334923", "Q51929311"]
            depths_dict[class_id] = get_class_depth(class_id,headers)
        # Find the class with the least depth
        coarsest_class = min(depths_dict, key=depths_dict.get)
    return coarsest_class

def get_pop(pageview_list:list)->int:
    """
    read views list from get_pageviews_data(), return a ceil average.
    """
    import math
    sub_pop = []
    for month in pageview_list:
        sub_pop.append(month['views'])
    try:
        sub_pop = math.ceil(sum(sub_pop)/len(sub_pop))
    except ZeroDivisionError:
        sub_pop = 0
    return sub_pop

def read_triples(filepath:str)->list:
    triples = []
    with open(filepath) as f:
        for line in f:
            data_instance = json.loads(line)
            triples.append(data_instance)
    return triples

def write_modification_file(output_path:str, results:list):# changed w to a, write whole results each time
    with open(output_path, 'a') as f:
        #for result in results:
        json.dump(results, f)  # JSON encode each element and write it to the file
        f.write('\n')

def add_sub_pop(file_path:str,wiki_path:str,headers:dict):
    kamel_list = [] #['config.json', 'P8875']
    for name in os.listdir(file_path):
        kamel_list.append(name)

    for file in os.listdir(wiki_path):# f is kamel PXX foler path
        p = file.strip('.jsonl')# P8594
        
        if p in kamel_list:
            sub_uri = []
            wiki = read_triples(os.path.join(wiki_path, file))
            for item in wiki:
                sub_uri.append(item['sub_uri'])

            f = os.path.join(file_path, p)
            test = read_triples(os.path.join(f, 'train.jsonl'))#读写哪块就改成对应的文件，test和output_path一致时只在原文件上更改

            output_path = os.path.join(f, 'train.jsonl')#这块2023.3.24号研究最终ensemble时下面查重部分注释掉，不需要单独文件，在原文件上添加pop即可#sub_uri.jsonl
            # if os.path.isfile(output_path):
            #     print("Sub URIs for {} already exist. Skipping file.".format(str(p)))
            #     continue

            for i in tqdm(range(len(test))):# iterate each test(triple) and add triple dict in the loop
                #for j in range(len(test[i]['index'])):
                wiki_index = test[i]['index'][0]
                triple = copy.copy(test[i])
                triple['sub_uri'] = wiki[wiki_index]['sub_uri']
                pagename = get_pagename(str(triple['sub_uri']),headers)
                page_data = get_pageviews_data(pagename,headers)
                instance_of_values = get_instance_of(str(triple['sub_uri']))
                coarsest_class = get_class(instance_of_values,headers)
                pop = get_pop(page_data)
                triple['sub_pagename'] = pagename
                triple['sub_pop'] = pop
                triple['class'] = coarsest_class
                write_modification_file(output_path, triple)
        else:
            continue

def add_obj_pop(file_path:str,headers:dict):
    for subdirectory in os.listdir(file_path):
        if subdirectory.startswith('P'):
            f = os.path.join(file_path, subdirectory)
        else:
            continue

        # checking if it is a file
        if os.path.isdir(f):
            test = read_triples(os.path.join(f, 'test.jsonl'))

        output_path = os.path.join(f, 'modified.jsonl')
        if os.path.isfile(output_path):
            print("Modification for {} already exist. Skipping file.".format(str(subdirectory)))
            continue

        for i in tqdm(range(len(test))):# iterate each test(triple) and add triple dict in the loop
            for j in range(len(test[i]['obj_uri'])):
                if test[i]['obj_uri'][j].startswith('Q'):
                    pagename = get_pagename(str(test[i]['obj_uri'][j]),headers)
                    page_data = get_pageviews_data(pagename,headers)
                    pop = get_pop(page_data)
                    triple = copy.copy(test[i])
                    triple['obj_pagename'] = pagename
                    triple['obj_pop'] = pop
                write_modification_file(output_path, triple) 


def main():
    headers = {
    "User-Agent": "Yuchao (y8.zhao@student.vu.nl)"
    }

    # parser = argparse.ArgumentParser(description='Get Pagenames with KAMEL URIs')
    # parser.add_argument('--input', help='Input folder path for KAMEL.')
    # args = parser.parse_args()

    wiki_path = '/Users/yuchaozhao/Downloads/enwiki_all_articles'

    file_path = '/Users/yuchaozhao/Downloads/practices/Thesis/KGC_LLMs/kamel_20_pop_class_full'#'/Users/yuchaozhao/Downloads/practices/Thesis/KGC_LLMs/kamel_20_pop_full'#args.input   'kamel_pop/kamel'     'kamel_pop/kamel_debug' 

    add_sub_pop(file_path,wiki_path,headers) 

    #add_obj_pop(file_path,headers)


if __name__ == "__main__":
    start = time.time()
    main()
    end = time.time()
    print('Time: ' + str(end-start))