from label_studio_sdk import Client

def main():
    # 连接到 Label Studio 服务
    client = Client(url="http://localhost:20004", api_key="9228983fcb7d2d5aa2179ca73616585b1a20713a")

    # 获取项目
    project = client.get_project(1)

    # 获取所有任务
    tasks = project.get_tasks()

    # 处理并输出标注数据
    for task in tasks:
        task_id = task['id']
        print(f"任务 ID: {task_id}")
        
        if 'annotations' in task and len(task['annotations']) > 0:
            # 打印完整的标注信息
            print("完整的标注数据:", task['annotations'])
            
            for annotation in task['annotations']:
                for result in annotation['result']:
                    # 打印 result 中的详细内容
                    print("标注结果详情:", result)
                    
                    # 如果包含 start 和 end 字段，输出高亮范围
                    if 'start' in result['value'] and 'end' in result['value']:
                        start = result['value']['start']
                        end = result['value']['end']
                        label = result['value']['labels'][0]
                        print(f"高亮范围: {start}-{end}, 标签: {label}")
                    else:
                        print("没有有效的高亮标注范围。")
        else:
            print(f"任务 ID: {task_id} 没有标注数据。")

if __name__ == "__main__":
    main()
