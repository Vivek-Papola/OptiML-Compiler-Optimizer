from dataset_gen import DatasetGenerator
import os

generator = DatasetGenerator()
folder_path = "./c_programs"
processed_file_list = "processed_files.txt"

# Load already processed files
if os.path.exists(processed_file_list):
    with open(processed_file_list, 'r') as f:
        processed_files = set(line.strip() for line in f)
else:
    processed_files = set()

# Process only new .c files
for file in os.listdir(folder_path):
    if file.endswith(".c") and file not in processed_files:
        full_path = os.path.join(folder_path, file)
        try:
            generator.process_file(full_path)
            processed_files.add(file)
            with open(processed_file_list, 'a') as f:
                f.write(file + "\n")
        except Exception as e:
            print(f"[!] Error processing {file}: {e}")
