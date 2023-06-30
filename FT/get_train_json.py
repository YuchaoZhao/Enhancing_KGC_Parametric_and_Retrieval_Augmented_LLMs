import csv
import json

file_path = '/home/yzhao/KAMEL/FT/train_set.csv'

data = []

with open(file_path, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # check if the value of the 'label' key contains a comma
        if ',' in row['label']:
            # split the value into a list
            row['label'] = row['label'].split(',')
        data.append(row)

with open('train_set_HF.json', 'w') as outfile:
    json.dump(data, outfile)