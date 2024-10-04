import os
import json
import argparse
import pandas as pd
from tqdm import tqdm


def merge_json2csv_file(result_dir, label_file, merge_file):
    if os.path.isfile(merge_file):
        os.remove(merge_file)

    result_data = {}
    json_files = [f for f in os.listdir(result_dir) if f.endswith(".json")]
    json_files.sort()
    for json_file in json_files:
        json_path = os.path.join(result_dir, json_file)
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            result_data[json_data["id"]] = json_data

    label_data = {}
    with open(label_file, mode='r', encoding='utf-8') as jsonl_file:
        for line in tqdm(jsonl_file, desc="Loading data"):
            json_data = json.loads(line.strip())
            label_data[json_data["id"]] = json_data

    merge_data = []
    for key in label_data:
        if key in result_data:
            merge_item = {**label_data[key], **result_data[key]}
            merge_data.append(merge_item)

    with open(json_path, 'r', encoding='utf-8') as f:
        df = pd.DataFrame(merge_data) 
        df.to_csv(merge_file, mode='w', index=False, encoding='utf-8')

    print(f"所有JSON文件已成功保存到 {merge_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge label result")
    parser.add_argument("--label_file", type=str, required=True, help="label file")
    parser.add_argument("--result_dir", type=str, required=True, help="result directory")
    parser.add_argument("--merge_file", type=str, required=True, help="merge file")
    args = parser.parse_args()

    merge_json2csv_file(args.result_dir, args.label_file, args.merge_file)
