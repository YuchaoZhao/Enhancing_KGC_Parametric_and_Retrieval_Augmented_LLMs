import json
import os
import pandas as pd

# Load the question templates
question_templates_path = "/Users/yuchaozhao/Downloads/practices/Thesis/KGC_LLMs/FT/question-templates_ft.csv"
question_templates_df = pd.read_csv(question_templates_path)
question_templates = question_templates_df[["prop", "question"]]

# Load the dataset
data_dir = "/Users/yuchaozhao/Downloads/practices/Thesis/KGC_LLMs/FT/kamel_with_sub_entity_pop_edited"
train_files = []#'/Users/yuchaozhao/Downloads/practices/Thesis/KGC_LLMs/FT/kamel_with_sub_entity_pop_edited/P136/train.jsonl'
prop = []
for subdir in os.listdir(data_dir):
    #print(subdir)#PXXX
    prop.append(subdir)
    subdir_path = os.path.join(data_dir, subdir)
    if os.path.isdir(subdir_path):
        train_files.append(os.path.join(subdir_path, "train.jsonl"))

train_dataset = []
for file in train_files:
    prop = os.path.basename(os.path.dirname(file))
    question = question_templates_df.loc[question_templates_df['prop'] == prop]['question'].iloc[0]
    with open(file, "r") as f:
        for line in f:
            triple = json.loads(line)
            question_line = question.replace('[S]', triple['sub_label'])
            train_dict = {}
            train_dict[question_line] = triple['obj_label']
            train_dataset.append(train_dict)

df = pd.DataFrame(columns=['text', 'label'])

for d in train_dataset:
    for key, value in d.items():
        text = key
        label = ', '.join(value)
        df = pd.concat([df, pd.DataFrame({'text': [text], 'label': [label]})], ignore_index=True)

df.to_csv('train_set.csv', index=False)

#print(df)
'''
                                                     text             label
0                 What is the genre of A Family Business?  contemporary R&B
1       What is the genre of Self Preserved While the ...  progressive rock
2                 What is the genre of Super Mario Bros.?     platform game
3                       What is the genre of Emery Tales?  documentary film
4                  What is the genre of Only Revolutions?  alternative rock
...                                                   ...               ...
206995      What ethnic group belonged Yu-Cheng Chang to?               Ami
206996        What ethnic group belonged Mária Földes to?     Jewish people
206997              What ethnic group belonged Liu He to?           Xiongnu
206998     What ethnic group belonged Periklis Drakos to?            Greeks
206999              What ethnic group belonged Kanosh to?           Pahvant

[207000 rows x 2 columns]
'''
