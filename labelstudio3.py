import requests
import re
from label_studio_sdk import Client

# 配置 XML
label_config = """
<View>
    <Header value="单张图片示例"/>
    <Style>
        .container {
            display: flex;
            justify-content: space-between;
        }
        .image-block {
            width: 50%;
        }
        .text-block {
            border: 1px solid #ccc;
            padding: 10px;
            width: 48%;
        }
    </Style>
    <View className="container">
        <View className="image-block">
            <Image name="url" value="$OriginalImage" maxWidth="100%"/>
        </View>
    </View>
    <View className="container">
        <View className="text-block">
            <Text name="overall_all_prompts" value="$Baseline"/>
            <Labels name="label1" toName="overall_all_prompts">
                <Label value="缺失(b)" background="red"/>
            </Labels>
        </View>
        <View className="text-block">
            <Text name="All_gt" value="$All_Others"/>
            <Labels name="label2" toName="All_gt">
                <Label value="缺失(g)" background="lavenderblush"/>
                <Label value="错误(g)" background="mistyrose"/>
            </Labels>
        </View>
        <View className="text-block">
            <Text name="After_merged" value="$Merged_Description"/>
            <Labels name="label3" toName="After_merged">
                <Label value="错误(m)" background="gold"/>
            </Labels>
        </View>      
    </View>
</View>
"""

def format_string_for_xml(input_string):
    if not isinstance(input_string, str):
        input_string = str(input_string) if input_string is not None else ''
    
    formatted_string = re.sub(r'\*\*(.*?)\*\*', r'\1', input_string)
    formatted_string = formatted_string.replace('<br><br>', '\n')
    
    return formatted_string

def list_projects(url, api_key):
    try:
        headers = {
            'Authorization': f'Token {api_key}'
        }
        response = requests.get(f'{url}/api/projects/', headers=headers)
        response.raise_for_status()
        projects_data = response.json()

        # 从 results 字段中获取项目列表
        projects = projects_data.get('results', [])

        print("Projects List:")
        for index, project in enumerate(projects):
            project_id = project.get('id')
            project_title = project.get('title')
            task_count = project.get('task_number', 0)
            annotation_count = project.get('num_tasks_with_annotations', 0)
            
            print(f"Index: {index}, ID: {project_id}, Title: {project_title}, Tasks: {task_count}, Annotations: {annotation_count}")

        return projects

    except Exception as e:
        print(f"Error listing projects: {e}")
        return []

def get_annotations_via_api(url, api_key, project_id):
    try:
        headers = {
            'Authorization': f'Token {api_key}'
        }
        response = requests.get(f'{url}/api/projects/{project_id}/tasks/', headers=headers)
        response.raise_for_status()
        tasks = response.json()
        
        # Debug: 打印获取的任务列表
        print("Tasks:", tasks)

        annotations = []
        for task in tasks:
            if 'annotations' in task:
                annotations.extend(task['annotations'])

        print(f"Total annotations fetched: {len(annotations)}")
        return annotations
    except Exception as e:
        print(f"Error fetching annotations via API: {e}")
        return None


def analyze_annotations(annotations):
    overall_label_counts = {}
    individual_counts = []

    for annotation in annotations:
        label_counts = {}
        
        # 检查 'result' 字段是否存在
        if 'result' in annotation:
            for result in annotation['result']:
                # 获取标签列表
                labels = result.get('value', {}).get('labels', [])
                for label in labels:
                    if label in label_counts:
                        label_counts[label] += 1
                    else:
                        label_counts[label] = 1

                    if label in overall_label_counts:
                        overall_label_counts[label] += 1
                    else:
                        overall_label_counts[label] = 1

        individual_counts.append(label_counts)
    
    # 计算平均每个 annotation 的标签数量
    total_annotations = len(annotations)
    average_counts = {label: count / total_annotations for label, count in overall_label_counts.items()}

    return individual_counts, overall_label_counts, average_counts

def main():
    url = 'http://localhost:20004'
    api_key = '9228983fcb7d2d5aa2179ca73616585b1a20713a'
    
    print("Fetching projects...")
    projects = list_projects(url, api_key)

    # 用户选择项目
    if projects:
        project_index = int(input("请选择项目索引: "))
        project_id = projects[project_index].get('id')
        
        print(f"Fetching project with ID: {project_id}")
        ls = Client(url=url, api_key=api_key)
        project = ls.get_project(project_id)
        print(f"Project fetched: {project}")

        # 用户输入任务 ID
        task_ids_input = input("请输入任务 ID，以逗号分隔: ")
        task_ids = [int(task_id.strip()) for task_id in task_ids_input.split(',')]

        # 导出指定任务的标注结果
        annotations = get_annotations_via_api(url, api_key, project_id)

        # 打印导出的标注结果
        if annotations:
            individual_counts, overall_counts, average_counts = analyze_annotations(annotations)
            
            print("Individual Annotation Label Counts:")
            for index, counts in enumerate(individual_counts):
                print(f"Annotation {index + 1}: {counts}")
            
            print("\nOverall Label Counts:", overall_counts)
            print("\nAverage Label Counts per Annotation:", average_counts)
        else:
            print("No annotations to display.")

if __name__ == "__main__":
    main()
