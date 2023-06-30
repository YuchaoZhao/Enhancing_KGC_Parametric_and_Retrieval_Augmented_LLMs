import pandas as pd

df = pd.read_csv('/Users/yuchaozhao/Downloads/practices/Thesis/KGC_LLMs/FT/datasets/dev_set.csv')#, header=None, names=['text']
df_sampled = df.sample(n=2000, random_state=42)
df_sampled.to_csv('dev_set_2000.csv', index=False)#, header=False
