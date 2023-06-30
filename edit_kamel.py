import json
import os
from tqdm import tqdm
import time

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

    file_path = '/Users/yuchaozhao/Downloads/practices/Thesis/KGC_LLMs/kamel_20_pop_class'#'/Users/yuchaozhao/Downloads/practices/Thesis/KAMEL/data/kamel_100/kamel'

    for subdirectory in os.listdir(file_path):
        results = []
        if subdirectory.startswith('P'):
            f = os.path.join(file_path, subdirectory)
        else:
            continue

        # checking if it is a file
        if os.path.isdir(f):
            test = read_triples(os.path.join(f, 'test.jsonl'))#(1)

        #for i in tqdm(range(len(test))):# iterate each test(triple) can add triple dict in the loop
        results = test[:50]#test[1000:]#选后1000个用来做预测，决定pop阈值

        output_path = os.path.join(f, 'test.jsonl')#(2)
        # if os.path.isfile(output_path):
        #     print("Edit for {} already exist. Skipping file.".format(str(subdirectory)))
        #     continue
        # 读（1）的内容写到（2）里
        write_modification_file(output_path, results)  

if __name__ == "__main__":
    start = time.time()
    main()
    end = time.time()
    print('Time: ' + str(end-start))