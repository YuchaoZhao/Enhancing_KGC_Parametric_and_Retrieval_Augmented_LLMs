# Modified based on https://github.com/JanKalo/KAMEL, https://huggingface.co/facebook/rag-token-nq

from transformers import RagTokenizer, RagRetriever, RagTokenForGeneration
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


def write_prediction_file(output_path, predictions):
    with open(output_path, 'w') as f:
        for prediction in predictions:
            json.dump(prediction, f)  # JSON encode each element and write it to the file
            f.write('\n')


def predict(s, p):
    prompt = create_fewshot(s, p)
    #inputs = tokenizer.prepare_seq2seq_batch(prompt, return_tensors="pt").to(0)
    inputs = tokenizer(prompt, return_tensors="pt").to(0)
    input_length = len(inputs["input_ids"].tolist()[0])
    #input_length = len(tokenizer(prompt, return_tensors="pt").to(0)["input_ids"].tolist()[0])
    #question_eos_token_id = AutoTokenizer.from_pretrained("facebook/dpr-question_encoder-single-nq-base").convert_tokens_to_ids('%')
    #generator_eos_token_id = AutoTokenizer.from_pretrained("facebook/bart-large").convert_tokens_to_ids('%')
    #eos_token_id=[int(question_eos_token_id),int(generator_eos_token_id)],
    #percent_id = tokenizer('%', return_tensors="pt")["input_ids"][0][0]
    output = model.generate(**inputs, 
                            max_length=input_length + LENGTH)#eos_token_id=int(stop_id),
    generated_text = tokenizer.decode(output[0].tolist(), skip_special_tokens=True)#batch_decode(output, skip_special_tokens=True)[0]
    # for c in generated_text:
    #     if '%' in c:
    #         generated_text = generated_text.split('%', 1)[0]
    new_text = generated_text.replace(prompt, '')
    return new_text.strip()


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
    parser.add_argument('--model', help='Put the huggingface model name here', default='facebook/rag-token-nq')
    parser.add_argument('--property', help='only evaluate a single property', default='')
    parser.add_argument('--input',
                        help='Input folder path. It needs to contain subfolders with property names containing train.jsonl and test.jsonl files.')
    parser.add_argument('--fewshot', help='Number of fewshot examples', default=0, type=int)
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


    tokenizer = RagTokenizer.from_pretrained("facebook/rag-token-nq")
    #tokenizer = AutoTokenizer.from_pretrained("facebook/rag-token-nq")

    #stop_id = tokenizer('%', return_tensors="pt")["input_ids"][0][1]

    retriever = RagRetriever.from_pretrained("facebook/rag-token-nq", index_name="exact")#legacy", "exact" and "compressed" , use_dummy_dataset=False

    model = RagTokenForGeneration.from_pretrained("facebook/rag-token-nq", retriever=retriever).to(0)
    

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
                    prediction = predict(triple['sub_label'], p)
                    # print("correct: ", triple["obj_label"])
                    result = {'sub_label': triple['sub_label'], 'relation': p, 'obj_label': triple['obj_label'],
                              'prediction': prediction, 'sub_pop': triple['sub_pop'], 'fewshotk': NUMBER}
                    results.append(result)

            write_prediction_file(output_path, results)
    end = time.time()
    print('Time: ' + str(end-start))
    print('Finished evaluation')
