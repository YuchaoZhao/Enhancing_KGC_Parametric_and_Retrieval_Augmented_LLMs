import requests
from ratelimit import limits
import json
import os
import copy
from tqdm import tqdm
import argparse
import time

# # [DO NOT DELETE]get_pageid is not used by now
# @limits(calls=50, period=1)# Set the rate limit to 50 requests per second
# def get_pageid(pagename:str,headers:dict)->int:
#     """
#     read pagename and return pageid
#     """
#     pageid_link = 'https://en.wikipedia.org/w/rest.php/v1/page/' + pagename
#     response = requests.get(pageid_link, headers=headers)
#     if response.status_code == 200:# Check if the request was successful
#         data = response.json()
#         pageid = data['id']
#     else:
#         print("Request id failed with status code:", response.status_code)
#     return pageid

# # [DO NOT DELETE]get_pageid is not used by now
# @limits(calls=50, period=1)# Set the rate limit to 50 requests per second
# def get_uri(pagename:str,pageid:int,headers:dict)->str:
#     """
#     read pagename and pageid, return uri
#     """
#     uri_link = 'https://en.wikipedia.org/w/api.php?action=query&prop=pageprops&titles=' + pagename + '&format=json'
#     response = requests.get(uri_link, headers=headers)
#     if response.status_code == 200:# Check if the request was successful
#         data = response.json()
#         uri = data['query']['pages'][str(pageid)]['pageprops']['wikibase_item']
#     else:
#         print("Request uri failed with status code:", response.status_code)
#     return uri


@limits(calls=50, period=1)# Set the rate limit to 70 requests per second
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

@limits(calls=50, period=1)# Set the rate limit to 70 requests per second
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

def get_pop(pageview_list:list)->int:
    """
    read views list from get_pageviews_data(), return a ceil average.
    """
    import math
    sub_pop = []
    for month in pageview_list:
        sub_pop.append(month['views'])
    sub_pop = math.ceil(sum(sub_pop)/len(sub_pop))
    return sub_pop


def read_triples(filepath:str):
    triples = []
    with open(filepath) as f:
        for line in f:
            data_instance = json.loads(line)
            triples.append(data_instance)
    return triples


def write_modification_file(output_path:str, results:list):
    with open(output_path, 'w') as f:
        for result in results:
            json.dump(result, f)  # JSON encode each element and write it to the file
            f.write('\n')


def main():
    headers = {
    "User-Agent": "Yuchao (y8.zhao@student.vu.nl)"
    }

    file_path = '/Users/yuchaozhao/Downloads/practices/Thesis/KAMEL/kamel_pop/kamel_debug'

    for subdirectory in os.listdir(file_path):
        results = []
        if subdirectory.startswith('P'):
            f = os.path.join(file_path, subdirectory)
        else:
            continue

        # checking if it is a file
        if os.path.isdir(f):
            test = read_triples(os.path.join(f, 'test.jsonl'))

        for i in tqdm(range(len(test))):# iterate each test(triple) can add triple dict in the loop
            for j in range(len(test[i]['obj_uri'])):
                if test[i]['obj_uri'][j].startswith('Q'):
                    pagename = get_pagename(str(test[i]['obj_uri'][j]),headers)
                    print(pagename)
                    page_data = get_pageviews_data(pagename,headers)
                    pop = get_pop(page_data)
                    triple = copy.copy(test[i])
                    triple['obj_pagename'] = pagename
                    triple['obj_pop'] = pop
                    results.append(triple)


        output_path = os.path.join(f, 'modified.jsonl')
        if os.path.isfile(output_path):
            print("Modification for {} already exist. Skipping file.".format(str(subdirectory)))
            continue

        write_modification_file(output_path, results)  

if __name__ == "__main__":
    start = time.time()
    main()
    end = time.time()
    print('Time: ' + str(end-start))