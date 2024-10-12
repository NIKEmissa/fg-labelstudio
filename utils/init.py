import pandas as pd
from datetime import datetime
import time
import os
from utils.label_tools import load_config, LabelStudioManager

# 返回每个任务的进度信息
def get_task_progress(manager, project_list):
    # 根据项目 ID 列表加载项目并统计完成度
    records = []
    for project_id in project_list:
        project = manager.load_project_by_id(project_id)
        if project:
            project_status = manager.get_project_status(project)
            records.append({
                'project_id': project_status['id'],
                'title': project_status['title'],
                'task_count': project_status['task_count'],
                'completed_count': project_status['completed_count'],
                'in_progress_count': project_status['in_progress_count'],
                'completion_percentage': project_status['completion_percentage'],
                'created_at': project_status['created_at'],
                'annotators': ', '.join(project_status['annotators']) if project_status['annotators'] else 'None',
                'absolute_completed': int(project_status['completion_percentage'] / 100 * project_status['task_count'])
            })
    completion_df = pd.DataFrame(records)
    total_row = pd.DataFrame([{
        'project_id': 'Total',
        'title': 'N/A',
        'task_count': completion_df['task_count'].sum(),
        'completed_count': completion_df['completed_count'].sum(),
        'in_progress_count': completion_df['in_progress_count'].sum(),
        'completion_percentage': completion_df['completion_percentage'].mean(),
        'created_at': 'N/A',
        'annotators': 'N/A',
        'absolute_completed': int(completion_df['absolute_completed'].sum())
    }])
    completion_df = pd.concat([completion_df, total_row], ignore_index=True)
    return completion_df

# 初始化函数
def initialize():
    # 加载配置
    config = load_config()
    config['labelstudio']['url'] = "http://zjstudio2024.top:20003"
    config['labelstudio']['api_key'] = "68d132dbafe046a52d91f620e29fabca8970568a"
    config['labelstudio']['external_ip'] = "zjstudio2024.top"

    # 创建 LabelStudioManager 实例
    manager = LabelStudioManager(config)

    # 定期查询任务完成度
    while True:
        # 查询任务完成度
        project_list = [project['id'] for project in manager.list_projects()]
        completion_df = get_task_progress(manager, project_list)

        # 添加请求时间
        request_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        completion_df['request_time'] = request_time

        # 重命名列
        completion_df.rename(columns={
            'project_id': 'project_id',
            'title': 'title',
            'task_count': 'total_tasks',
            'completed_count': 'completed_tasks',
            'in_progress_count': 'in_progress_tasks',
            'completion_percentage': 'completion_percentage',
            'created_at': 'created_at',
            'annotators': 'annotators'
        }, inplace=True)

        # 保存至 CSV 文件
        progress_dir = 'progress'
        if not os.path.exists(progress_dir):
            os.makedirs(progress_dir)
        csv_file = os.path.join(progress_dir, f'task_completion_summary_{request_time}.csv')
        completion_df.to_csv(csv_file, index=False)

        print(f"任务完成度已保存至 {csv_file}")

        # 每 10 分钟查询一次
        time.sleep(600)

if __name__ == "__main__":
    initialize()