import json
from collections import defaultdict

# 读取 JSON 文件
def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# 统计模块
def statistics(json_data):
    label_counts = defaultdict(int)
    detection_counts = defaultdict(int)
    custom_labels_counts = defaultdict(int)
    custom_detection_counts = defaultdict(int)
    label_text_counts = defaultdict(lambda: defaultdict(int))
    total_annotations = len(json_data)
    
    # 遍历所有标注数据
    for annotation in json_data:
        # 统计与 'overall_all_prompts' 相关的标注数据
        for result in annotation.get('annotations', []):
            for label in result.get('result', []):
                label_type = label.get('type')
                value = label.get('value')
                
                if label_type == 'labels' and value:
                    # 统计字段 "labels"
                    for selected_label in value['labels']:
                        label_counts[selected_label] += 1
                        label_text = value.get('text', '')
                        if label_text:
                            label_text_counts[selected_label][label_text] += 1

                elif label_type == 'rectanglelabels' and value:
                    # 统计字段 "rectanglelabels"
                    for detection_label in value['rectanglelabels']:
                        detection_counts[detection_label] += 1

                elif label_type == 'textarea' and value:
                    # 统计字段 "custom-label-input" 和 "custom-label-input-detection"
                    if label['from_name'] == 'custom-label-input':
                        for custom_label in value['text']:
                            custom_labels_counts[custom_label] += 1
                    elif label['from_name'] == 'custom-label-input-detection':
                        for custom_label in value['text']:
                            custom_detection_counts[custom_label] += 1

    return label_counts, detection_counts, custom_labels_counts, custom_detection_counts, label_text_counts, total_annotations

# 打印数据
def print_statistics(label_counts, detection_counts, custom_labels_counts, custom_detection_counts, label_text_counts, total_annotations):
    print("\n===== 标签统计 =====")
    for label, count in label_counts.items():
        average = count / total_annotations if total_annotations > 0 else 0
        print(f"{label}: {count} (平均: {average:.2f})")

    print("\n===== 丢失细节框统计 =====")
    for label, count in detection_counts.items():
        average = count / total_annotations if total_annotations > 0 else 0
        print(f"{label}: {count} (平均: {average:.2f})")

    print("\n===== 自定义标签统计 =====")
    for label, count in custom_labels_counts.items():
        average = count / total_annotations if total_annotations > 0 else 0
        print(f"{label}: {count} (平均: {average:.2f})")

    print("\n===== 自定义丢失细节标签统计 =====")
    for label, count in custom_detection_counts.items():
        average = count / total_annotations if total_annotations > 0 else 0
        print(f"{label}: {count} (平均: {average:.2f})")

    print("\n===== 标签对应文字统计 =====")
    for label, text_dict in label_text_counts.items():
        print(f"\n{label}:")
        for text, count in text_dict.items():
            print(f"  '{text}': {count}")

# 主函数
def main():
    file_path = '/data1/A800-01/data/xinzhedeng/MyCode/Project/labelstudio/utils/project-6-at-2024-10-05-01-11-f328877d.json'  # 请替换为你的 JSON 文件路径
    json_data = read_json(file_path)
    label_counts, detection_counts, custom_labels_counts, custom_detection_counts, label_text_counts, total_annotations = statistics(json_data)
    print_statistics(label_counts, detection_counts, custom_labels_counts, custom_detection_counts, label_text_counts, total_annotations)

if __name__ == "__main__":
    main()