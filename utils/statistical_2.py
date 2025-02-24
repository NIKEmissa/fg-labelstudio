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

    # 初始化任务 ID 集合
    task_ids = set()

    # 遍历 DataFrame 的每一行，统计标签
    for index, row in df.iterrows():
        from_name = row['模型']
        label = row['标签']
        task_id = row['id']  # 获取任务 ID
        
        # 将任务 ID 添加到集合中
        task_ids.add(task_id)
        
        model_id = next((model_id_map[key] for key in model_id_map if key in from_name), -1)
        dimension = next((dimension_map[key] for key in dimension_map if key in from_name), '未知')

        # 统计标签和相应的模型id和维度
        label_counter_by_model[model_id].update([(label, dimension)])  # 更新为标签和维度的组合

    # 统计任务量
    task_count = len(task_ids)

    # 准备透视表数据
    table_data = []
    for model_id in sorted(label_counter_by_model.keys()):
        for (label, dimension), count in label_counter_by_model[model_id].items():
            table_data.append([model_id, label, dimension, count])

    # 创建 DataFrame
    df_result = pd.DataFrame(table_data, columns=["模型id", "标签", "维度", "统计次数"])

    # 使用透视表
    df_pivot = df_result.pivot_table(index='模型id', columns=['标签', '维度'], values='统计次数', fill_value=0)

    # 将任务量添加到透视表的最左第二列
    df_pivot.insert(0, '任务量', task_count)

    # 打印表格
    print(tabulate(df_pivot.fillna(0).reset_index().values, headers=df_pivot.reset_index().columns, tablefmt="grid"))

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

    # 根据 id、标签、模型 id 去重
    df = df.drop_duplicates(subset=['id', '标签', '模型'])

    # 使用 Counter 记录每个模型的标签统计
    label_counter_by_model = defaultdict(Counter)

    # 使用集合统计唯一任务数量根据 "原图URL"
    unique_task_ids = set(df['原图URL'])
    task_count = len(unique_task_ids)

    # 遍历 DataFrame 的每一行，统计标签
    for _, row in df.iterrows():
        from_name = row['模型']
        label = row['标签']
        model_id = next((model_id_map[key] for key in model_id_map if key in from_name), -1)
        dimension = next((dimension_map[key] for key in dimension_map if key in from_name), '未知')

        # 统计标签和相应的模型 id 和维度
        if model_id is not None and dimension is not None:
            label_counter_by_model[model_id].update([(label, dimension)])

    # 准备透视表数据
    table_data = []
    for model_id in sorted(label_counter_by_model.keys()):
        for (label, dimension), count in label_counter_by_model[model_id].items():
            table_data.append([model_id, task_count, label, dimension, count])

    # 创建 DataFrame
    df_result = pd.DataFrame(table_data, columns=["模型id", "任务量", "标签", "维度", "统计次数"])

    # 使用透视表
    df_pivot = df_result.pivot_table(index='模型id', columns=['标签', '维度'], values='统计次数', fill_value=0)
    df_pivot.insert(0, '任务量', task_count)

    # 打印表格
    print(tabulate(df_pivot.fillna(0).values, headers=df_pivot.columns, tablefmt="grid"))

    return df_pivot
    
import pandas as pd

# 定义处理DataFrame的函数
def process_annotations(df):
    # 按照annotation_id分组，将标注类型为'补充文本'的行进行分组并转换为字典
    supplementary_texts = df[df['标注类型'] == '补充文本'].groupby('annotation_id')['标签'].apply(list).to_dict()

    # 定义函数，用于将补充文本追加到非补充文本的行
    def append_supplementary(row):
        if row['annotation_id'] in supplementary_texts:
            return supplementary_texts[row['annotation_id']]
        return []

    # 应用该函数创建“自定义文本”列
    df['自定义文本'] = df.apply(append_supplementary, axis=1)
    
    # 删除标注类型为“补充文本”的行
    df = df[df['标注类型'] != '补充文本']
    
    return df
    
def collect_raw_annotations_info(annotations):
    print(annotations)
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
        url = annotation.get('data', {}).get('url', '') or annotation.get('image_url', '')  # 获取原图信息
        print(url)

        for result in results:
            from_name = result.get('from_name', '')
            annotation_id = result.get('id', '')
            print(result)
            text = result.get('value', {}).get('text', '')
            model_id = next((model_id_map[key] for key in model_id_map if key in from_name), None)
            dimension = next((dimension_map[key] for key in dimension_map if key in from_name), None)
            
            # 处理 labels 类型
            if result.get('type') == 'labels':
                labels = result.get('value', {}).get('labels', [])
                for label in labels:
                    raw_data.append({
                        'id': task_id,
                        '标注类型': 'labels',
                        'annotation_id': annotation_id,
                        '模型': from_name,
                        '标签': label,
                        '标注文本': text,
                        'created_username': created_username,
                        '模型id': model_id,
                        '维度': dimension,
                        '原图URL': url
                    })
            # 处理 choices 类型
            elif result.get('type') == 'choices':
                choices = result.get('value', {}).get('choices', [])
                for choice in choices:
                    raw_data.append({
                        'id': task_id,
                        '标注类型': 'choices',
                        '模型': from_name,
                        'annotation_id': annotation_id,                        
                        '标签': choice,
                        '标注文本': text,
                        'created_username': created_username,
                        '模型id': model_id,
                        '维度': dimension,
                        '原图URL': url
                    })
                    
            # 处理 rectanglelabels 类型
            elif result.get('type') == 'rectanglelabels':
                rectangle_labels = result.get('value', {}).get('rectanglelabels', [])
                for rectangle_label in rectangle_labels:
                    raw_data.append({
                        'id': task_id,
                        '标注类型': 'rectanglelabels',
                        '模型': from_name,
                        'annotation_id': annotation_id,
                        '标签': rectangle_label,
                        '标注文本': text,
                        'created_username': created_username,
                        '模型id': model_id,
                        '维度': dimension,
                        '原图URL': url
                    })                  
                    
            # 处理 textarea 类型
            elif result.get('type') == 'textarea':
                textarea_labels = result.get('value', {}).get('text', [])
                for textarea_label in textarea_labels:
                    raw_data.append({
                        'id': task_id,
                        '标注类型': '补充文本',
                        '模型': from_name,
                        'annotation_id': annotation_id,
                        '标签': textarea_label,
                        '标注文本': '',
                        'created_username': created_username,
                        '模型id': model_id,
                        '维度': dimension,
                        '原图URL': url
                    })                                        

    # 创建 DataFrame
    df_raw = pd.DataFrame(raw_data)
    df_raw = process_annotations(df_raw)
    return df_raw


def merge_annotations_by_project_ids(project_id_list, manager):
    all_raw_data = []

    for project_id in project_id_list:
        print(f'Fetching annotations for project ID: {project_id}')
        loaded_project = manager.load_project_by_id(project_id)
        annotations = manager.get_all_annotations(loaded_project)  # 假设这是获取标注的函数
        project_status = manager.get_project_status(loaded_project)
        
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
        # manager.list_projects()

        # 通过 URL 加载项目示例
        # project_url = 'http://218.28.238.77:20003/projects/262/data?tab=214'  # 修改为你的项目 URL
        # project_url = 'http://zjstudio2024.top:20003/projects/184/data?tab=146'  # 修改为你的项目 URL
        # project_url = 'http://zjstudio2024.top:20003/projects/53/data?tab=30'
        # loaded_project = manager.load_project_by_url(project_url)
#         loaded_project = manager.load_project_by_id('53')

#         print(f"Loaded project: {loaded_project}")
        
#         annotations = manager.get_all_annotations(loaded_project)
#         print(annotations)        
        
#         project_status = manager.get_project_status(loaded_project)
#         print(project_status)    
        
#         parse_and_count_labels_from_annotations(annotations)
        
        # # 算法文生图
        # project_list = ['52', '53', '54', '55', '56', '57', '58', '59', '60', '61', '62', '63', '66', '123', '124', '125', '126', '127', '128', '129', '130', '131', '132', '133', '134']
        
        # 专家文生图
        # project_list = [
        #     '160', '177', '163', '169', '172', '180', '182', '146', '135', '138', '140', '148', '147',
        #     '162', '179', '167', '171', '174', '181', '183', '152', '154', '150', '156', '164', '168',
        #     '176', '173', '158', '149', '187', '188', '185', '184'
        # ]

        ###### 专家 文生图 图生文 结果汇总 #########
        
        # 专家文生图
        project_list = [
            '160', '177', '163', '169', '172', '180', '182', '146', '135', '138', '140', '148', '147',
            '162', '179', '167', '171', '174', '181', '183', '152', '154', '150', '156', '164', '168',
            '176', '173', '158', '149', '187', '188', '185', '184'
        ]
        
        # # 专家图生文
        # project_list = ['74', '75', '76', '77', '78', '79', '81', '82', '83', '86', '88', '89', '92', '94', '95', '90', '99', '91', '105', '80', '194', '195', '196', '102', '106', '104', '103', '197', '198', '199', '200', '202', '203', '204', '206', '207']
        
        df = merge_annotations_by_project_ids(project_list, manager)        
        df.to_csv('resutls_zhuanjia.csv')
    
        df2 = parse_and_count_labels_from_csv(df)
        df2.to_csv('results_zhuanjia_image_to_text_1006.csv')        
        
        df3 = parse_and_count_unique_labels_from_csv(df)
        df3.to_csv('results_zhuanjia_set_image_to_text_1006.csv')
        
        
        ###### 算法 文生图 结果汇总 #########

#         # 算法图生文
#         project_list = ["65", "113", "114", "115", "116", "117", "118", "119", "120", "121", "122", "64", "201", "205", "208", "210", "211", "212", "215", "216", "217"]
#         # project_list = ["219"]

        
#         df = merge_annotations_by_project_ids(project_list, manager)        
#         df.to_csv('resutls_suanfa.csv')
    
#         df2 = parse_and_count_labels_from_csv(df)
#         df2.to_csv('results_suanfa_image_to_text_1006.csv')        
        
#         df3 = parse_and_count_unique_labels_from_csv(df)
#         df3.to_csv('results_suanfa_set_image_to_text_1006.csv')        
        