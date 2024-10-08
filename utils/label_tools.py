import os
import pandas as pd
import re
import yaml
from label_studio_sdk import Client
import tiktoken

def count_tokens(text, model="gpt-4o"):
    """计算给定文本的 token 数量"""
    enc = tiktoken.encoding_for_model(model)
    tokens = enc.encode(text)
    return len(tokens)

def load_config(config_path='./config/config.yaml'):
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)   
    
def get_column_index(df, column_name):
    try:
        return df.columns.get_loc(column_name)
    except KeyError:
        return 0

def format_string_for_xml(input_string):
    if not isinstance(input_string, str):
        input_string = str(input_string) if input_string is not None else ''
    
    # Replace ** text** with text
    formatted_string = re.sub(r'\*\*(.*?)\*\*', r'\1', input_string)
    
    # Replace <br><br> with \n
    formatted_string = formatted_string.replace('<br><br>', '\n')
    
    return formatted_string

def convert_to_html_and_escape_xml(text):
    try:
        # 转换加粗文本为 HTML 格式
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)        
        return text
    except Exception as e:
        # 如果转换失败，返回原文本
        print(f"Conversion failed: {e}")
        return text

def abc(config, df):
    # 初始化 Label Studio Client
    url = config['labelstudio']['url']
    api_key = config['labelstudio']['api_key']
    print(f"Initializing Label Studio Client with URL: {url} and API Key: {api_key}")
    ls = Client(url=url, api_key=api_key)

    # 创建新项目
    print("Creating new project...")
    project = ls.start_project(
        title='New Fashion Project',
        label_config=config['label_config']
    )
    print("Project created successfully.")

    # 创建任务
    tasks = []
    print("Creating tasks...")
    for index, row in df.iterrows():
        task_data = {
            'data': {
                'OriginalImage': row['url'],
                'Baseline': format_string_for_xml(row['image_caption_cn']),
                'Baseline_token_cnt': count_tokens(format_string_for_xml(row['image_caption_cn'])),
                'Baseline_EN': format_string_for_xml(row['image_caption_en']),
                'Baseline_EN_token_cnt': count_tokens(format_string_for_xml(row['image_caption_en'])),
                'All_Others': format_string_for_xml(row['all_others_cn']),
                'All_Others_token_cnt': count_tokens(format_string_for_xml(row['all_others_cn'])),
                'All_Others_EN': format_string_for_xml(row['all_others_en']),
                'All_Others_EN_token_cnt': count_tokens(format_string_for_xml(row['all_others_en'])),
                'Merged_Description': format_string_for_xml(row['merged_caption_cn']),
                'Merged_Description_token_cnt': count_tokens(format_string_for_xml(row['merged_caption_cn'])),
                'Merged_Description_EN': format_string_for_xml(row['merged_caption_en']),
                'Merged_Description_EN_token_cnt': count_tokens(format_string_for_xml(row['merged_caption_en']))
            }
        }
        tasks.append(task_data)
        print(f"Task {index} created: {task_data}")

    # 打印所有任务以检查格式
    print("All tasks created:")
    for task in tasks:
        print(task)

    # 批量导入任务
    print("Importing tasks into project...")
    try:
        task_ids = project.import_tasks(tasks)
        print("Tasks imported successfully.")

        # 使用正确的外网 IP 打印项目数据页面 URL
        external_ip = config['labelstudio']['external_ip']  # 使用配置中的外网 IP
        project_data_url = f"http://{external_ip}:20004/projects/{project.id}/data/"
        print(f"Project data URL: {project_data_url}")
        return project_data_url

    except Exception as e:
        print(f"Error importing tasks: {e}")
        return None

def flux_models(config, df):
    # 初始化 Label Studio Client
    url = config['labelstudio']['url']
    api_key = config['labelstudio']['api_key']
    print(f"Initializing Label Studio Client with URL: {url} and API Key: {api_key}")
    ls = Client(url=url, api_key=api_key)

    # 创建新项目
    print("Creating new project...")
    project = ls.start_project(
        title='New Fashion Project',
        label_config=config['label_config']
    )
    print("Project created successfully.")

    # 创建任务
    tasks = []
    print("Creating tasks...")
    for index, row in df.iterrows():
        task_data = {
            'data': {
                'OriginalImage': row['url'],
                'Baseline': format_string_for_xml(row['image_caption_cn']),
                'Baseline_token_cnt': count_tokens(format_string_for_xml(row['image_caption_cn'])),
                'Baseline_EN': format_string_for_xml(row['image_caption_en']),
                'Baseline_EN_token_cnt': count_tokens(format_string_for_xml(row['image_caption_en'])),
                'M1': row['url1'],
                'M2': row['url2'],
                'M3': row['url3'],
            }
        }
        tasks.append(task_data)
        print(f"Task {index} created: {task_data}")

    # 打印所有任务以检查格式
    print("All tasks created:")
    for task in tasks:
        print(task)

    # 批量导入任务
    print("Importing tasks into project...")
    try:
        task_ids = project.import_tasks(tasks)
        print("Tasks imported successfully.")

        # 使用正确的外网 IP 打印项目数据页面 URL
        external_ip = config['labelstudio']['external_ip']  # 使用配置中的外网 IP
        external_port = self.config['labelstudio']['external_port']
        project_data_url = f"http://{external_ip}:{external_port}/projects/{project.id}/data/"
        print(f"Project data URL: {project_data_url}")
        return project_data_url

    except Exception as e:
        print(f"Error importing tasks: {e}")
        return None
    
# 新增的 LabelStudioManager 类
class LabelStudioManager:
    def __init__(self, config):
        """
        初始化 LabelStudioManager，登录到 Label Studio。
        """
        self.config = config
        self.client = self.login()
        self.validate_config()

    def login(self):
        """
        登录到 Label Studio 并返回客户端实例。
        """
        url = self.config['labelstudio']['url']
        api_key = self.config['labelstudio']['api_key']
        print(f"Initializing Label Studio Client with URL: {url} and API Key: {api_key}")
        client = Client(url=url, api_key=api_key)
        return client

    def validate_config(self):
        """验证配置的完整性"""
        required_keys = [
            'url', 
            'api_key', 
            'external_ip', 
            'external_port', 
        ]
        for key in required_keys:
            if key not in self.config['labelstudio']:
                raise ValueError(f"Missing required configuration key: {key}")

    def list_projects(self):
        """
        列出 Label Studio 中所有现有项目。
        """
        projects = self.client.get_projects()
        project_list = []
        print("Listing all projects:")
        for project in projects:
            project_info = {
                'id': project.id,
                'title': project.title,
                'created_at': project.created_at
            }
            project_list.append(project_info)
            print(project_info)
        return project_list

    def create_project(self, title='New Fashion Project', task_type='merge_compare'):
        """
        创建一个新的项目，并返回项目对象。
        """
        if task_type == 'merge_compare':
            label_config = self.config['label_config']
        elif task_type == 'flux_models_compare':
            label_config = self.config['flux_models_config']
        elif task_type == 'flux_models_compare_text':
            label_config = self.config['flux_models_text_config']            
        elif task_type == 'image_to_text_compare':
            label_config = self.config['image_to_text_config']
        elif task_type == 'text_to_image_compare':
            label_config = self.config['text_to_image_config']
        else:
            label_config = self.config['label_config']

        print("Creating new project...")
        project = self.client.start_project(
            title=title,
            label_config=label_config
        )
        print(f"Project '{title}' created successfully with ID: {project.id}")
        return project    

    def upload_task(self, project, task_data):
        """
        向指定项目上传单条任务，并返回上传状态。
        """
        print(f"Uploading task to project ID {project.id}: {task_data}")
        try:
            project.import_tasks([task_data])
            print("Task uploaded successfully.")
            return True
        except Exception as e:
            print(f"Error uploading task: {e}")
            return False

    def upload_tasks_bulk(self, project, tasks):
        """
        向指定项目批量上传任务，并返回上传状态。
        """
        print(f"Uploading {len(tasks)} tasks to project ID {project.id}...")
        try:
            project.import_tasks(tasks)
            print("All tasks uploaded successfully.")
            return True
        except Exception as e:
            print(f"Error uploading tasks: {e}")
            return False

    def get_all_annotations(self, project):
        """
        返回指定项目的所有标注结果。
        """
        print(f"Fetching all annotations for project ID {project.id}...")
        annotations = []
        try:
            tasks = project.get_tasks()
            for task in tasks:
                # 从 annotations 字段获取标注结果
                for annotation in task.get('annotations', []):
                    annotations.append(annotation)
            print(f"Retrieved {len(annotations)} annotations.")
            return annotations
        except Exception as e:
            print(f"Error fetching annotations: {e}")
            return annotations

    def get_project_status(self, project):
        """
        列出指定项目的状态信息，包括任务完成百分比和标注人。
        """
        print(f"Fetching statistics for project ID {project.id}...")
        try:
            tasks = project.get_tasks()
            total_tasks = len(tasks)
            completed_count = sum(1 for task in tasks if task['annotations'])
            in_progress_count = total_tasks - completed_count
            completion_percentage = (completed_count / total_tasks * 100) if total_tasks > 0 else 0

            # 提取标注人信息
            annotators = set()
            for task in tasks:
                for annotation in task.get('annotations', []):
                    username = annotation.get('created_username')
                    if username:
                        # 去掉后面的数字
                        username_cleaned = username.split(',')[0].strip()
                        annotators.add(username_cleaned)

            status = {
                'id': project.id,
                'title': project.title,
                'task_count': total_tasks,
                'completed_count': completed_count,
                'in_progress_count': in_progress_count,
                'completion_percentage': completion_percentage,
                'created_at': project.created_at,
                'annotators': list(annotators)  # 记录所有标注人
            }
            print(f"Project Status: {status}")
            return status
        except Exception as e:
            print(f"Error fetching project status: {e}")
            return {}

    def get_project_data_url(self, project):
        """
        返回项目数据页面的外网 URL。
        """
        external_ip = self.config['labelstudio']['external_ip']  # 使用配置中的外网 IP
        external_port = self.config['labelstudio']['external_port']
        project_data_url = f"http://{external_ip}:{external_port}/projects/{project.id}/data/"
        print(f"Project data URL: {project_data_url}")
        return project_data_url
    
    def load_project_by_url(self, project_url):
        """
        通过项目 URL 加载项目。
        """
        try:
            project_id = project_url.split('/')[-2]  # 获取项目 ID
            project = self.client.get_project(project_id)
            print(f"Loaded project with ID: {project.id} from URL: {project_url}")
            return project
        except Exception as e:
            print(f"Error loading project from URL: {e}")
            return None

    def load_project_by_id(self, project_id):
        """
        通过项目 ID 加载项目。
        """
        try:
            project = self.client.get_project(project_id)
            print(f"Loaded project with ID: {project.id} ")
            return project
        except Exception as e:
            print(f"Error loading project with ID: {e}")
            return None
        
    def get_projects_completion_df(self, project_ids):
        """
        根据项目 ID 列表加载多个项目，统计每个项目的完成度，并返回 DataFrame。
        """
        records = []
        for project_id in project_ids:
            project = self.load_project_by_id(project_id)
            if project:
                project_status = self.get_project_status(project)
                for username in project_status['annotators']:
                    records.append({
                        'project_id': project.id,
                        'created_username': username,
                        'completion_percentage': project_status['completion_percentage']
                    })
        return pd.DataFrame(records)

if __name__ == '__main__':
    run_example = 4
    
    if run_example == 1:
        # 加载配置
        config = load_config()

        # 读取 CSV 文件
        csv_path = '/data1/A800-01/data/xinzhedeng/MyCode/Project/labelstudio/output2_2024-09-25 06:54:50.csv'
        print(f"Reading CSV file from: {csv_path}")
        df = pd.read_csv(csv_path)

        # 调用原有的 abc 函数
        print("\n=== 使用原有的 abc 函数 ===")
        project_data_url_abc = abc(config, df)
        if project_data_url_abc:
            print(f"Label Studio project (abc) is available at: {project_data_url_abc}")
        else:
            print("Failed to create and upload tasks to the Label Studio project via abc().")

        # 新增：使用 LabelStudioManager 类进行操作
        print("\n=== 使用 LabelStudioManager 类 ===")
        label_manager = LabelStudioManager(config)

        # 示例 1: 创建项目，读取 CSV，逐条上传任务
        print("\n--- 示例 1: 创建项目并逐条上传任务 ---")
        project = label_manager.create_project(title='New Fashion Project via Class')

        print(f"Reading CSV file from: {csv_path}")
        df = pd.read_csv(csv_path)

        print("Uploading tasks one by one...")
        for index, row in df.iterrows():
            task_data = {
                'data': {
                    'OriginalImage': row['url'],
                    'Baseline': format_string_for_xml(row['image_caption_cn']),
                    'Baseline_token_cnt': count_tokens(format_string_for_xml(row['image_caption_cn'])),
                    'Baseline_EN': format_string_for_xml(row['image_caption_en']),
                    'Baseline_EN_token_cnt': count_tokens(format_string_for_xml(row['image_caption_en'])),
                    'All_Others': format_string_for_xml(row['all_others_cn']),
                    'All_Others_token_cnt': count_tokens(format_string_for_xml(row['all_others_cn'])),
                    'All_Others_EN': format_string_for_xml(row['all_others_en']),
                    'All_Others_EN_token_cnt': count_tokens(format_string_for_xml(row['all_others_en'])),
                    'Merged_Description': format_string_for_xml(row['merged_caption_cn']),
                    'Merged_Description_token_cnt': count_tokens(format_string_for_xml(row['merged_caption_cn'])),
                    'Merged_Description_EN': format_string_for_xml(row['merged_caption_en']),
                    'Merged_Description_EN_token_cnt': count_tokens(format_string_for_xml(row['merged_caption_en']))
                }
            }
            success = label_manager.upload_task(project, task_data)
            if success:
                print(f"Task {index} uploaded successfully.")
            else:
                print(f"Failed to upload Task {index}.")

        # 示例 2: 获取项目的所有信息
        print("\n--- 示例 2: 获取项目的所有信息 ---")
        project_status = label_manager.get_project_status(project)
        annotations = label_manager.get_all_annotations(project)
        project_url = label_manager.get_project_data_url(project)
        print(f"Project Status: {project_status}")
        print(f"Number of Annotations: {len(annotations)}")
        print(f"Project Data URL: {project_url}")
        
        
    elif run_example == 2:
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
        loaded_project = manager.load_project_by_url(project_url)

        annotations = manager.get_all_annotations(loaded_project)
        print(annotations)        
        
        project_status = manager.get_project_status(loaded_project)
        print(project_status)
        
    elif run_example == 3:
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
        loaded_project = manager.load_project_by_url(project_url)

        annotations = manager.get_all_annotations(loaded_project)
        print(annotations)        
        
        project_status = manager.get_project_status(loaded_project)
        print(project_status)
        
    # 在 run_example 中使用示例
    elif run_example == 4:
        # 加载配置
        config = load_config()    

        # 自定义config配置
        config['labelstudio']['url'] = "http://zjstudio2024.top:20003"
        config['labelstudio']['api_key'] = "68d132dbafe046a52d91f620e29fabca8970568a"
        config['labelstudio']['external_ip'] = "zjstudio2024.top"        

        # 创建 LabelStudioManager 实例
        manager = LabelStudioManager(config)

        # 根据项目 ID 列表加载项目并统计完成度
#         project_list = ["184", "185"]
#         project_list = [
#         '123', '124', '125', '126', '127', '128', '129', '131', '132', '133', '134',
#         '52', '53', '66', '55', '56', '57', '58', '59', '60', '61', '62', '63'
#         ]        
        
#         # 专家文生图
#         project_list = [
#             '160', '177', '163', '169', '172', '180', '182', '146', '135', '138', '140', '148', '147',
#             '162', '179', '167', '171', '174', '181', '183', '152', '154', '150', '156', '164', '168',
#             '176', '173', '158', '149', '187', '188', '185', '184'
#         ]        
        project_list = ["123", "130", "133"]

        completion_df = manager.get_projects_completion_df(project_list)

        # 输出 DataFrame
        print(completion_df)       
        
        completion_df.to_csv('completion_df.csv')