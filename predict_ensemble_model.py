# Modified based on https://github.com/JanKalo/KAMEL, https://huggingface.co/facebook/rag-token-nq

from transformers import RagTokenizer, RagRetriever, RagTokenForGeneration, AutoModelForCausalLM, AutoTokenizer
import argparse
import json
import os
import random
from tqdm import tqdm
import torch as torch
import time

start = time.time()

LENGTH = 100
FAST_TOKENIZATION = False
RANDOM = False
NUMBER = 10
test = []
train = []
templates = {}

# retrieve prompt and create single triple prompt
def create_prompt_for_triple(s, p):
    template = templates[p]
    template = template.replace('[S]', s)
    return template


# get k fewshot examples from triple list and create prompt
# this works also for number = 0

def create_fewshot(s, p):
    prompt = ""
    if NUMBER != 0:
        sample = random.sample(train, NUMBER)
        for triple in sample:
            few_s = triple['sub_label']
            few_o = "; ".join(triple['obj_label'])
            prompt += create_prompt_for_triple(few_s, p)
            prompt += " {}%\n".format(few_o)#有改动%
    prompt += create_prompt_for_triple(s, p)
    return prompt

def create_zeroshot(s, p):
    prompt = ""
    prompt += create_prompt_for_triple(s, p)
    return prompt

def write_prediction_file(output_path, predictions):
    with open(output_path, 'w') as f:
        for prediction in predictions:
            json.dump(prediction, f)  # JSON encode each element and write it to the file
            f.write('\n')


def predict(s, p):
    prompt = create_fewshot(s, p)
    question = create_zeroshot(s, p)
    # #rag
    # inputs_rag = tokenizer_rag(question, return_tensors="pt").to(0)
    # input_length_rag = len(inputs_rag["input_ids"].tolist()[0])
    # output_rag = model_rag.generate(**inputs_rag, 
    #                         max_length=input_length_rag + LENGTH)
    # generated_text_rag = tokenizer_rag.decode(output_rag[0].tolist(), skip_special_tokens=True)
    # new_text_rag = generated_text_rag.replace(question, '')
    # rag = new_text_rag.strip()
    #opt
    inputs_opt = tokenizer_opt(prompt, return_tensors="pt").to(0)
    input_length_opt = len(inputs_opt["input_ids"].tolist()[0])
    output_opt = model_opt.generate(**inputs_opt, eos_token_id=int(tokenizer_opt.convert_tokens_to_ids("%")),
                            max_length=input_length_opt + LENGTH)
    generated_text_opt = tokenizer_opt.decode(output_opt[0].tolist(), skip_special_tokens=True)
    new_text_opt = generated_text_opt.replace(prompt, '')
    opt = new_text_opt.strip()
    #rag_ft
    inputs_ft = tokenizer_ft(question, return_tensors="pt").to(0)
    input_length_ft = len(inputs_ft["input_ids"].tolist()[0])
    output_ft = model_ft.generate(**inputs_ft, 
                            max_length=input_length_ft + LENGTH)
    generated_text_ft = tokenizer_ft.decode(output_ft[0].tolist(), skip_special_tokens=True)
    new_text_ft = generated_text_ft.replace(question, '')
    new_text_ft.strip()
    ft = new_text_ft.strip()

    return opt,ft#rag,


def read_triples(filepath):
    triples = []
    with open(filepath) as f:
        for line in f:
            data_instance = json.loads(line)
            triples.append(data_instance)
    return triples


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='KAMEL Generative Model Predictions')
    parser.add_argument('--model', help='Put the huggingface model name here', default='ensemble')
    parser.add_argument('--property', help='only evaluate a single property', default='')
    parser.add_argument('--input',
                        help='Input folder path. It needs to contain subfolders with property names containing train.jsonl and test.jsonl files.')
    parser.add_argument('--fewshot', help='Number of fewshot examples', default=10, type=int)
    parser.add_argument('--templates', help='Path to template file')
    parser.add_argument('--fast', help='activates the fast tokenizer. This might not work with OPT.',
                        action='store_true')

    args = parser.parse_args()
    FAST_TOKENIZATION = args.fast

    NUMBER = args.fewshot
    model_name = args.model
    file_path = args.input
    template_path = args.templates
    if ',' in args.property:
        property = args.property.split(',')
    else:
        property = [args.property]


    # tokenizer_rag = RagTokenizer.from_pretrained("facebook/rag-token-nq")
    # retriever_rag = RagRetriever.from_pretrained("facebook/rag-token-nq", index_name="exact")
    # model_rag = RagTokenForGeneration.from_pretrained("facebook/rag-token-nq", retriever=retriever_rag).to(0)

    tokenizer_opt = AutoTokenizer.from_pretrained("facebook/opt-13b", use_fast=False)
    model_opt = AutoModelForCausalLM.from_pretrained("facebook/opt-13b", torch_dtype=torch.float16).to(0)
   
    tokenizer_ft = RagTokenizer.from_pretrained("facebook/rag-token-base")
    retriever_ft = RagRetriever.from_pretrained("facebook/rag-token-base", index_name="exact")
    model_ft = RagTokenForGeneration.from_pretrained("/home/yzhao/KAMEL/FT/large_ft/output_dir/checkpoint2/", retriever=retriever_ft).to(0)

    print('Read parameters')
    print("Model {}\nShots {}\nProperties {}".format(model_name,NUMBER,property))
    print('Loaded {} model from huggingface.'.format(model_name))
    with open(template_path) as f:
        for line in f:
            p, t = line.split(',')
            templates[p] = t.replace('\n', '')
    print('Loaded template file from {}'.format(template_path))

    for subdirectory in os.listdir(file_path):
        results = []
        f = os.path.join(file_path, subdirectory)
        # checking if it is a file
        if os.path.isdir(f):
            train = read_triples(os.path.join(f, 'train.jsonl'))
            test = read_triples(os.path.join(f, 'test.jsonl'))

            #parse p from directory name
            p = str(subdirectory)

            output_path = os.path.join(f, 'predictions_{}_fewshot_{}.jsonl'.format(model_name.replace('/', ''), NUMBER))
            if os.path.isfile(output_path):
                print("Predictions for {} already exist. Skipping file.".format(str(subdirectory)))
                continue

            # if property parameter is chosen, continue until in the right subdirectory
            if property != [''] and p not in property:
                continue
            if p in templates:
                print('Evaluate examples for property {}'.format(p))
                for triple in tqdm(test):
                    opt,ft = predict(triple['sub_label'], p)#rag,
                    if triple['model'] == 'OPT':
                        prediction = opt.replace('%','')                
                    else:
                        prediction = ft
                    # print("correct: ", triple["obj_label"])
                    result = {'sub_label': triple['sub_label'], 'relation': p, 'obj_label': triple['obj_label'],
                              'prediction': prediction, 'sub_pop': triple['sub_pop'], 'entity_class': triple['class'], 'model': triple['model'], 'fewshotk': NUMBER}
                    results.append(result)

            write_prediction_file(output_path, results)
    end = time.time()
    print('Time: ' + str(end-start))
    print('Finished evaluation')
