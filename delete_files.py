import os
import shutil

# specify the path of the parent folder
parent_folder_path = "/Users/yuchaozhao/Downloads/practices/Thesis/KAMEL/kamel_with_sub_entity_pop_edited"

# loop through all subfolders in the parent folder that start with "P"
for folder_name in os.listdir(parent_folder_path):
    if folder_name.startswith("P"):
        # get the full path of the sub_uri.jsonl file
        file_path = os.path.join(parent_folder_path, folder_name, "sub_uri.jsonl")
        # check if the file exists and delete it
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted {file_path}")
