import json
import pandas as pd
from collections import defaultdict

# 从 JSON 文件读取最小字段库
def load_min_fields(json_file):
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data.get('en2cn', {})

# 从 TXT 文件读取目标文本库
def load_target_texts(txt_file):
    cloth_count = defaultdict(int)

    with open(txt_file, 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip():  # 确保不是空行
                data = json.loads(line)
                cloth_list = data.get("captions", {}).get("cloth", [])
                for cloth in cloth_list:
                    items = [item.strip() for item in cloth.split(',')]
                    for item in items:
                        if " with " in item:
                            left, right = item.split(" with ", 1)
                            cloth_count[left.strip()] += 1
                            cloth_count[right.strip()] += 1
                        else:
                            cloth_count[item] += 1
    return list(cloth_count.items())  # 返回累积的计数列表

def parse_texts(target_texts, min_fields):
    results = []
    overall_counts = {keyword: 0 for keyword in min_fields.keys()}  # 初始化计数器

    for text, count in target_texts:
        matched_fields = {}
        for keyword, translation in min_fields.items():
            occurrences = text.count(keyword) * count  # 计数关键字在文本中的出现次数并乘以总出现次数
            if occurrences > 0:
                matched_fields[keyword] = occurrences  # 记录出现次数
                overall_counts[keyword] += occurrences  # 更新总计数
        if matched_fields:
            results.append({
                "original_text": text,
                "matched_fields": matched_fields
            })

    return results, overall_counts  # 返回解析结果和整体计数

# 保存计数到 CSV 文件
def save_counts_to_csv(overall_counts, output_file):
    sorted_counts = sorted(overall_counts.items(), key=lambda x: x[1], reverse=True)
    df = pd.DataFrame(sorted_counts, columns=['Keyword', 'Count'])
    df.to_csv(output_file, index=False, encoding='utf-8')

# 加载最小字段库和目标文本库
min_fields = load_min_fields('/data1/A800-01/data/xinzhedeng/MyCode/Misc/labels_fg13_with_en_-_ch.json')
target_texts = load_target_texts('/data1/datasets/dress_v20_t2i_mulpose.flist')

# 执行解析
parsed_results, overall_counts = parse_texts(target_texts, min_fields)

# 打印结果
for result in parsed_results:
    print(result)

# 保存整体计数到 CSV 文件
output_csv = '/data1/A800-01/data/xinzhedeng/MyCode/Misc/cloth_count_results.csv'
save_counts_to_csv(overall_counts, output_csv)

print(f"Overall keyword counts saved to {output_csv}.")
