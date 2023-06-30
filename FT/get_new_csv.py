import pandas as pd

# # 1. For Train and Dev and Test-text

# # Load the CSV file into a pandas dataframe
# df = pd.read_csv('/Users/yuchaozhao/Downloads/practices/Thesis/KGC_LLMs/FT/datasets/large/test_set_2000.csv')

# # Get the column you want by name
# column_name = 'text'
# column_data = df[column_name]

# # Create a new dataframe with just the column data
# new_df = pd.DataFrame({column_name: column_data})#column_data

# # Save the new dataframe to a new CSV file
# new_df.to_csv('RAG_test_text_2000.csv', index=False)

# 2. For Test-label

# Load the CSV file into a pandas dataframe
df = pd.read_csv('/Users/yuchaozhao/Downloads/practices/Thesis/KGC_LLMs/FT/datasets/large/test_set_2000.csv')

chosen_values = df['label'].apply(lambda x: eval(x)[0]['chosen'])

# Save the new dataframe to a new CSV file
chosen_values.to_csv('RAG_test_label_2000.csv', index=False)