import os
import uuid
from datetime import datetime
import streamlit as st
import pandas as pd
from utils.label_tools import load_config

# 全局日志队列
log_queue = []
import threading

lock = threading.Lock()

# 记录推理日志
def log_inference(result_url, username, others=None):
    log_id = str(uuid.uuid4())  # 生成唯一的 UUID
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 获取当前时间戳
    
    # 将 others 字典转换为字符串
    others_str = ', '.join([f'"{key}": "{value}"' for key, value in (others or {}).items()]) if others else "{}"
    others_str = "{" + others_str + "}"  # 包装成字典格式字符串
    
    with lock:
        log_queue.append((log_id, result_url, username, timestamp, others_str))  # 记录日志
        # 将日志写入文件
        with open("inference_log.txt", "a") as f:
            f.write(f"{log_id}, {result_url}, {username}, {timestamp}, {others_str}\n")

# 读取日志
def read_log():
    logs = []
    if os.path.exists("inference_log.txt"):
        with open("inference_log.txt", "r") as f:
            logs = f.readlines()
    return logs

# 推理日志页面
def log_page():
    # 日志页面
    st.title("推理日志记录")
    logs = read_log()
    log_data = []

    for log in logs:
        parts = log.strip().split(', ')
        # 处理新老格式
        if len(parts) >= 4:
            if len(parts) > 4:  # 当存在额外部分时，尝试解析字典
                others_str = parts[4:]
            else:
                others_str = "{}"  # 老格式，没有字典，显示空字典
            
            log_data.append(parts[:4] + [others_str])  # 仅将前四个字段和字典字符串添加到数据中

    log_df = pd.DataFrame(log_data, columns=["Uuid", "Result URL", "Username", "Timestamp", "Others"])
    st.table(log_df)

    # 显示最新任务进度
    st.title("任务进度监控")
    show_latest_progress()

# 显示最新任务进度
@st.fragment(run_every="10s")
def show_latest_progress():
    # 显示更新按钮，用户可以手动刷新进度
    st.button("更新进度")
    
    with st.expander("任务进度数据读取"):
        # 查找最新的 CSV 文件
        progress_dir = 'progress'
        if not os.path.exists(progress_dir):
            st.write("未找到任何任务进度记录。")
            return

        csv_files = [f for f in os.listdir(progress_dir) if f.endswith('.csv')]
        if not csv_files:
            st.write("未找到任何任务进度记录。")
            return

        latest_csv = max(csv_files, key=lambda x: datetime.strptime(x.split('_')[-1].replace('.csv', ''), '%H-%M-%S') if len(x.split('_')[-1].split('-')) == 3 else datetime.min)
        latest_csv_path = os.path.join(progress_dir, latest_csv)

        # 读取最新的进度数据
        completion_df = pd.read_csv(latest_csv_path)
        st.write(f"自动更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.table(completion_df)

    with st.expander("任务进度条"):
        # 为每个任务显示进度条
        for _, row in completion_df.iterrows():
            st.write(f"任务: {row['project_id']}")
            st.progress(row['completion_percentage'] / 100)

    with st.expander("任务进度可视化"):
        # 可视化每个任务的进度
        st.write("### 每个任务的进度监控")
        st.bar_chart(data=completion_df.set_index('project_id')['completion_percentage'])

# 主函数，运行 Streamlit 页面
if __name__ == "__main__":
    # 加载配置
    config = load_config()
    config['labelstudio']['url'] = "http://zjstudio2024.top:20003"
    config['labelstudio']['api_key'] = "68d132dbafe046a52d91f620e29fabca8970568a"
    config['labelstudio']['external_ip'] = "zjstudio2024.top"

    # 运行日志页面
    log_page()