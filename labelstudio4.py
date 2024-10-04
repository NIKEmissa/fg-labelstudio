import pandas as pd
from label_studio_sdk import Client

# 读取CSV文件
csv_path = '/data1/A800-01/data/xinzhedeng/MyCode/Project/labelstudio/output2_2024-09-24 13:38:54.csv'
print(f"Reading CSV file from: {csv_path}")
df = pd.read_csv(csv_path)
print("CSV Data Loaded:")
print(df.head())  # 打印前几行数据，检查格式

# 初始化 Label Studio Client
url = 'http://localhost:20004'
api_key = '9228983fcb7d2d5aa2179ca73616585b1a20713a'
print(f"Initializing Label Studio Client with URL: {url} and API Key: {api_key}")
ls = Client(url=url, api_key=api_key)

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
        }
        .text-block-left, .text-block-right {
            width: 40%; /* 两边的文本框宽度 */
        }
        .text-block-center {
            width: 20%; /* 中间的文本框宽度 */
        }
        .highlight-bold {
            font-weight: bold;
            background-color: yellow; /* 高亮背景色 */
            padding: 2px;
        }
    </Style>
    <View className="container">
        <View className="image-block">
            <Image name="url" value="$OriginalImage" maxWidth="100%"/>
        </View>
    </View>
    <View className="container">
        <View className="text-block text-block-left">
            <Text name="overall_all_prompts" value="$Baseline"/>
            <Labels name="label1" toName="overall_all_prompts">
                <Label value="缺失(b)" background="red"/>
            </Labels>
        </View>
        <View className="text-block text-block-center">
            <Text name="All_gt" value="$All_Others"/>
            <Labels name="label2" toName="All_gt">
                <Label value="缺失(g)" background="red"/>
                <Label value="错误(g)" background="gold"/>
            </Labels>
        </View>
        <View className="text-block text-block-right">
            <HyperText name="After_merged" value="$Merged_Description"/>
            <Labels name="label3" toName="After_merged">
                <Label value="错误(m)" background="gold"/>
                <Label value="新增(m)" background="green"/>                
            </Labels>
        </View>      
    </View>
</View>

"""

# 创建新项目
print("Creating new project...")
project = ls.start_project(
    title='New Fashion Project',
    label_config=label_config
)
print("Project created successfully.")

# 创建任务
tasks = []
print("Creating tasks...")
for index, row in df.iterrows():
    if index > 2: break
    task_data = {
        'data': {
            'OriginalImage': row['url'],  # 确保这个字段名与项目配置匹配
            'Baseline': row['image_caption_cn'],  # 确保这个字段名与项目配置匹配
            'All_Others': row['all_others_cn'],
            'Merged_Description': "abcd<a>test</a>abcd"  # 加粗和高亮
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
    external_ip = '218.28.238.77'  # 使用正确的外网 IP
    project_data_url = f"http://{external_ip}:20004/projects/{project.id}/data/"
    print(f"Project data URL: {project_data_url}")
        
except Exception as e:
    print(f"Error importing tasks: {e}")
