import csv
import json
import argparse
from tqdm import tqdm


def read_jsonl_file(jsonl_file_path):
    json_objects = []

    with open(jsonl_file_path, mode='r', encoding='utf-8') as jsonl_file:
        for line in jsonl_file:
            json_obj = json.loads(line.strip())
            json_objects.append(json_obj)

    return json_objects


def convert_csv2jsonl_label(csv_file_path, jsonl_file_path):
    with open(csv_file_path, mode='r', encoding='utf-8') as csv_file, \
        open(jsonl_file_path, mode='w', encoding='utf-8') as jsonl_file:
        
        csv_reader = csv.DictReader(csv_file)
        id_counter = 1
        
        for row in csv_reader:
            category = row.get("category", "None")
            json_obj = {
                "id": id_counter,
                "category": category,
                "goods_id": int(row['goods_id']),
                "url": row['url'],
            }
            
            json_line = json.dumps(json_obj, ensure_ascii=False)
            jsonl_file.write(json_line + '\n')
            id_counter += 1

    print(f'CSV 文件已成功转换为 JSON Lines 文件，保存在 {jsonl_file_path}')


def convert_csv2jsonl_merge(csv_file_path, jsonl_file_path):
    with open(csv_file_path, mode='r', encoding='utf-8') as csv_file, \
        open(jsonl_file_path, mode='w', encoding='utf-8') as jsonl_file:
        
        csv_reader = csv.DictReader(csv_file)
        id_counter = 1
        
        for row in csv_reader:
            category = row.get("category", "None")
            json_obj = {
                "id": id_counter,
                "category": category,
                "goods_id": int(row['goods_id']),
                "url": row['url'],
                "All_prompts": row['All_prompts'],
                "All_gt": row['All_gt']
            }
            
            json_line = json.dumps(json_obj, ensure_ascii=False)
            jsonl_file.write(json_line + '\n')
            id_counter += 1

    print(f'CSV 文件已成功转换为 JSON Lines 文件，保存在 {jsonl_file_path}')


def convert_csv2jsonl_transl(csv_file_path, jsonl_file_path):
    with open(csv_file_path, mode='r', encoding='utf-8') as csv_file, \
        open(jsonl_file_path, mode='w', encoding='utf-8') as jsonl_file:
        
        csv_reader = csv.DictReader(csv_file)
        id_counter = 1
        
        for row in csv_reader:
            category = row.get("category", "None")
            json_obj = {
                "id": id_counter,
                "category": category,
                "goods_id": int(row['goods_id']),
                "url": row['url'],
                "text": row['text'],
            }
            
            json_line = json.dumps(json_obj, ensure_ascii=False)
            jsonl_file.write(json_line + '\n')
            id_counter += 1

    print(f'CSV 文件已成功转换为 JSON Lines 文件，保存在 {jsonl_file_path}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge label result")
    parser.add_argument("--csv_file", type=str, default="data/merge_baseline_gt.csv")
    parser.add_argument("--jsonl_file", type=str, default="output/debug_label/debug_label_100.jsonl")
    parser.add_argument("--convert_merge", action="store_true")
    parser.add_argument("--convert_label", action="store_true")
    parser.add_argument("--convert_transl", action="store_true")
    args = parser.parse_args()

    assert not (args.convert_label and args.convert_merge) and (args.convert_label or args.convert_merge)
    if args.convert_label:
        convert_csv2jsonl_label(args.csv_file, args.jsonl_file)
    elif args.convert_merge:
        convert_csv2jsonl_merge(args.csv_file, args.jsonl_file)
    elif args.convert_transl:
        convert_csv2jsonl_transl(args.csv_file, args.jsonl_file)
