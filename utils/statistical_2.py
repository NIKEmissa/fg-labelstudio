import json
import os
import csv
from collections import defaultdict, Counter
import re
from tabulate import tabulate  # 用于生成表格
import pandas as pd

def sort_from_name_key(name):
    # 使用正则提取 'label' 后的数字，用于排序
    match = re.search(r'(\d+)', name)
    return int(match.group(1)) if match else 0

def parse_and_count_labels_by_model_in_order(folder_path):
    # 用于保存标签的计数器，按模型划分
    label_counter_by_model = defaultdict(Counter)
    image_count_by_json = []

    # 遍历指定文件夹中的所有 JSON 文件
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            json_file_path = os.path.join(folder_path, filename)
            print(f'处理文件: {json_file_path}')
            
            # 打开并加载 JSON 文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 记录当前 JSON 文件的打标图片数量
            image_count = len(data)  # 假设每个任务对应一张图片
            image_count_by_json.append((filename, image_count))
            
            # 遍历每个任务，收集标注中的标签值
            for task in data:
                annotations = task.get('annotations', [])
                for annotation in annotations:
                    results = annotation.get('result', [])
                    for result in results:
                        # 处理 labels 类型
                        if result.get('type') == 'labels':
                            labels = result.get('value', {}).get('labels', [])
                            from_name = result.get('from_name', '')
                            # 统计每个模型下的标签
                            label_counter_by_model[from_name].update(labels)
                        # 处理 choices 类型
                        elif result.get('type') == 'choices':
                            choices = result.get('value', {}).get('choices', [])
                            from_name = result.get('from_name', '')
                            # 统计每个模型下的 choices
                            label_counter_by_model[from_name].update(choices)

    # 按顺序（label1-cloth, label2-cloth...）排序并生成统计结果
    sorted_models = sorted(label_counter_by_model.keys(), key=sort_from_name_key)

    # 准备第一个表格数据
    table_data = []
    for model in sorted_models:
        for label, count in label_counter_by_model[model].items():
            table_data.append([model, label, count])
    
    # 打印第一个表格
    headers = ["模型", "标签", "统计次数"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

    # 准备第二个表格数据
    image_table_data = [(filename, count) for filename, count in image_count_by_json]
    
    # 打印第二个表格
    image_headers = ["文件名", "打标图片数量"]
    print(tabulate(image_table_data, headers=image_headers, tablefmt="grid"))

    # 将第一个表格写入 CSV 文件
    with open('label_statistics.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)  # 写入表头
        writer.writerows(table_data)  # 写入数据

    # 将第二个表格写入 CSV 文件
    with open('image_counts.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(image_headers)  # 写入表头
        writer.writerows(image_table_data)  # 写入数据

def parse_and_count_labels_from_annotations(annotations):
    label_counter_by_model = defaultdict(Counter)
    
    for annotation in annotations:
        results = annotation.get('result', [])
        for result in results:
            # 处理 labels 类型
            if result.get('type') == 'labels':
                labels = result.get('value', {}).get('labels', [])
                from_name = result.get('from_name', '')
                label_counter_by_model[from_name].update(labels)
            # 处理 choices 类型
            elif result.get('type') == 'choices':
                choices = result.get('value', {}).get('choices', [])
                from_name = result.get('from_name', '')
                label_counter_by_model[from_name].update(choices)

    # 按顺序（label1-cloth, label2-cloth...）排序并生成统计结果
    sorted_models = sorted(label_counter_by_model.keys(), key=sort_from_name_key)

    # 准备表格数据
    table_data = []
    for model in sorted_models:
        for label, count in label_counter_by_model[model].items():
            table_data.append([model, label, count])
    
    # 打印表格
    headers = ["模型", "标签", "统计次数"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

# def parse_and_count_labels_from_csv(df):
#     label_counter_by_model = defaultdict(Counter)

#     # 定义模型 ID 和维度的映射
#     model_id_map = {
#         'label1': 1,
#         'label2': 2,
#         'label3': 3,
#         'label4': 4
#     }
    
#     dimension_map = {
#         'cloth': '服装',
#         'fabric': '面料',
#         'generator-side': '生图侧',
#         'others': '其它',
#     }

#     # 遍历 DataFrame 的每一行，统计标签
#     for index, row in df.iterrows():
#         from_name = row['模型']
#         label = row['标签']
#         model_id = next((model_id_map[key] for key in model_id_map if key in from_name), None)
#         dimension = next((dimension_map[key] for key in dimension_map if key in from_name), None)
        
#         # 统计标签和相应的模型id和维度
#         label_counter_by_model[from_name].update([label])

#     # 按顺序（label1-cloth, label2-cloth...）排序并生成统计结果
#     sorted_models = sorted(label_counter_by_model.keys(), key=sort_from_name_key)

#     # 准备表格数据
#     table_data = []
#     for model in sorted_models:
#         for label, count in label_counter_by_model[model].items():
#             # 将模型id和维度也加入到表格数据中
#             model_id = next((model_id_map[key] for key in model_id_map if key in model), None)
#             dimension = next((dimension_map[key] for key in dimension_map if key in model), None)
#             table_data.append([model, label, count, model_id, dimension])

#     # 创建 DataFrame
#     df_result = pd.DataFrame(table_data, columns=["模型", "标签", "统计次数", "模型id", "维度"])

#     # 打印表格
#     print(tabulate(df_result.values, headers=df_result.columns, tablefmt="grid"))

#     return df_result  # 返回结果的 DataFrame

def parse_and_count_labels_from_csv(df):
    label_counter_by_model = defaultdict(Counter)

    # 定义模型 ID 和维度的映射
    model_id_map = {
        'label1': 1,
        'label2': 2,
        'label3': 3,
        'label4': 4
    }
    
    dimension_map = {
        'cloth': '服装',
        'fabric': '面料',
        'generator-side': '生图侧',
        'others': '其它',
    }

    # 遍历 DataFrame 的每一行，统计标签
    for index, row in df.iterrows():
        from_name = row['模型']
        label = row['标签']
        model_id = next((model_id_map[key] for key in model_id_map if key in from_name), None)
        dimension = next((dimension_map[key] for key in dimension_map if key in from_name), None)
        
        # 统计标签和相应的模型id和维度
        label_counter_by_model[model_id].update([(label, dimension)])  # 更新为标签和维度的组合

    # 准备透视表数据
    table_data = []
    for model_id in sorted(label_counter_by_model.keys()):
        for (label, dimension), count in label_counter_by_model[model_id].items():
            table_data.append([model_id, label, dimension, count])

    # 创建 DataFrame
    df_result = pd.DataFrame(table_data, columns=["模型id", "标签", "维度", "统计次数"])

    # 使用透视表
    df_pivot = df_result.pivot_table(index='模型id', columns=['标签', '维度'], values='统计次数', fill_value=0)

    # 打印表格
    print(tabulate(df_pivot.fillna(0).values, headers=df_pivot.columns, tablefmt="grid"))

    return df_pivot  # 返回透视结果的 DataFrame

def parse_and_count_unique_labels_from_csv(df):
    # 定义模型 ID 和维度的映射
    model_id_map = {
        'label1': 1,
        'label2': 2,
        'label3': 3,
        'label4': 4
    }
    
    dimension_map = {
        'cloth': '服装',
        'fabric': '面料',
        'generator-side': '生图侧',
        'others': '其它',
    }

    # 使用一个集合来记录每个 ID 下的标签
    unique_labels_by_id = defaultdict(set)
    id_count_by_model = defaultdict(set)  # 记录每个模型 ID 的唯一 ID 数量

    # 遍历 DataFrame 的每一行，统计标签
    for index, row in df.iterrows():
        task_id = row['id']  # 假设 DataFrame 中有 'id' 列
        from_name = row['模型']
        label = row['标签']
        model_id = next((model_id_map[key] for key in model_id_map if key in from_name), None)
        dimension = next((dimension_map[key] for key in dimension_map if key in from_name), None)
        
        # 添加标签到对应 ID 的集合中
        if model_id is not None and dimension is not None:
            unique_labels_by_id[task_id].add((label, model_id, dimension))
            id_count_by_model[model_id].add(task_id)  # 记录模型 ID 对应的任务 ID

    # 准备统计数据
    label_counter_by_model = defaultdict(int)
    for labels in unique_labels_by_id.values():
        for label, model_id, dimension in labels:
            label_counter_by_model[(model_id, label, dimension)] += 1

    # 准备透视表数据
    table_data = []
    for (model_id, label, dimension), count in label_counter_by_model.items():
        id_count = len(id_count_by_model[model_id])  # 获取该模型 ID 的唯一 ID 数量
        table_data.append([model_id, label, dimension, count, id_count])  # 添加 ID 数量

    # 创建 DataFrame
    df_result = pd.DataFrame(table_data, columns=["模型id", "标签", "维度", "统计次数", "唯一ID数量"])

    # 使用透视表
    df_pivot = df_result.pivot_table(index='模型id', columns=['标签', '维度'], values='统计次数', fill_value=0)

    # 打印表格
    print(tabulate(df_pivot.fillna(0).values, headers=df_pivot.columns, tablefmt="grid"))

    return df_pivot  # 返回透视结果的 DataFrame


    
def collect_raw_annotations_info(annotations):
    raw_data = []

    # 定义模型 ID 和维度的映射
    model_id_map = {
        'label1': 1,
        'label2': 2,
        'label3': 3,
        'label4': 4
    }
    
    dimension_map = {
        'cloth': '服装',
        'fabric': '面料',
        'generator-side': '生图侧',
        'others': '其它',
    }

    for annotation in annotations:
        task_id = annotation.get('id')
        created_username = annotation.get('created_username', '')
        results = annotation.get('result', [])

        for result in results:
            from_name = result.get('from_name', '')
            model_id = next((model_id_map[key] for key in model_id_map if key in from_name), None)
            dimension = next((dimension_map[key] for key in dimension_map if key in from_name), None)
            
            # 处理 labels 类型
            if result.get('type') == 'labels':
                labels = result.get('value', {}).get('labels', [])
                for label in labels:
                    raw_data.append({
                        'id': task_id,
                        '模型': from_name,
                        '标签': label,
                        'created_username': created_username,
                        '模型id': model_id,
                        '维度': dimension
                    })
            # 处理 choices 类型
            elif result.get('type') == 'choices':
                choices = result.get('value', {}).get('choices', [])
                for choice in choices:
                    raw_data.append({
                        'id': task_id,
                        '模型': from_name,
                        '标签': choice,
                        'created_username': created_username,
                        '模型id': model_id,
                        '维度': dimension
                    })

    # 创建 DataFrame
    df_raw = pd.DataFrame(raw_data)
    return df_raw



def merge_annotations_by_project_ids(project_id_list, manager):
    all_raw_data = []

    for project_id in project_id_list:
        print(f'Fetching annotations for project ID: {project_id}')
        loaded_project = manager.load_project_by_id(project_id)
        annotations = manager.get_all_annotations(loaded_project)  # 假设这是获取标注的函数
        
        if annotations:
            raw_data = collect_raw_annotations_info(annotations)  # 使用之前定义的函数
            all_raw_data.append(raw_data)

    # 合并所有 DataFrame
    merged_df = pd.concat(all_raw_data, ignore_index=True)
    return merged_df

if __name__ == "__main__":
    run_example = 2
    if run_example == 1:
        # 测试从文件夹读取的功能
        folder_path = '/data1/A800-01/data/xinzhedeng/MyCode/Project/labelstudio/results/'  # 替换为你的文件夹路径
        parse_and_count_labels_by_model_in_order(folder_path)
        
    elif run_example == 2:
        from label_tools import LabelStudioManager, load_config
        
        # 加载配置
        config = load_config()    
        
        # 自定义config配置
        config['labelstudio']['url'] = "http://zjstudio2024.top:20003"
        config['labelstudio']['api_key'] = "68d132dbafe046a52d91f620e29fabca8970568a"
        config['labelstudio']['external_ip'] = "zjstudio2024.top"        

        # 创建 LabelStudioManager 实例
        manager = LabelStudioManager(config)

        # 列出所有项目
        manager.list_projects()

        # 通过 URL 加载项目示例
        project_url = 'http://218.28.238.77:20003/projects/262/data?tab=214'  # 修改为你的项目 URL
        project_url = 'http://zjstudio2024.top:20003/projects/184/data?tab=146'  # 修改为你的项目 URL
        project_url = 'http://zjstudio2024.top:20003/projects/53/data?tab=30'
        # loaded_project = manager.load_project_by_url(project_url)
#         loaded_project = manager.load_project_by_id('53')

#         print(f"Loaded project: {loaded_project}")
        
#         annotations = manager.get_all_annotations(loaded_project)
#         print(annotations)        
        
#         project_status = manager.get_project_status(loaded_project)
#         print(project_status)    
        
#         parse_and_count_labels_from_annotations(annotations)
        
        project_list = ['52', '53', '54', '55', '56', '57', '58', '59', '60', '61', '62', '63', '66', '123', '124', '125', '126', '127', '128', '129', '130', '131', '132', '133', '134']
        # project_list = ['52', '53', '54', '55', '56', '57', '58', '59', '60', '61', '62', '63', '66']
        # project_list = ['123', '124', '125', '126', '127', '128', '129', '130', '131', '132', '133', '134']
        # project_list = ['123', '124', '125', '126', '127', '128', '129', '130', '131', '132', '133', '134']

        # # 专家图生文
        # project_list = [
        #      '74', '75', '76', '77', '78', '79', '81', '82', '83', '86', '88', '89', '92', '94', '95', '97', '90', '98', '87', '99', '100', '91', '105', '80', '102', '106', '104', '103'
        # ]   
        
        # # 专家文生图
        # project_list = [
        #     '160', '177', '163', '169', '172', '180', '182', '146', '135', '138', '140', '148', '147',
        #     '162', '179', '167', '171', '174', '181', '183', '152', '154', '150', '156', '164', '168',
        #     '176', '173', '158', '149', '187', '188', '185', '184'
        # ]
        # df = merge_annotations_by_project_ids(['52', '53', '54', '55', '56', '57', '58', '59', '60', '61', '62', '63', '64', '65', '66'], manager)
        # df = merge_annotations_by_project_ids(['123', '124', '125', '126', '127', '128', '129', '130', '131', '132', '133', '134'], manager)        
        df = merge_annotations_by_project_ids(project_list, manager)        

#         df.to_csv('resutls.csv')
#         print(df.head())
    
#         df2 = parse_and_count_labels_from_csv(df)
#         # df2.to_csv('results_zhuanjia_text_to_image_1006.csv')
#         df2.to_csv('results_zhuanjia_image_to_text_1006.csv')        
        
        df3 = parse_and_count_unique_labels_from_csv(df)
        df3.to_csv('results_set_text_to_image_1006.csv')        
