# logging.py

import os
import uuid
from datetime import datetime
from queue import Queue
import threading
import streamlit as st
import pandas as pd

# 全局日志队列
log_queue = Queue()
lock = threading.Lock()

def log_inference(result_url, username):
    log_id = str(uuid.uuid4())  # 生成唯一的 UUID
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 获取当前时间戳
    with lock:
        log_queue.put((log_id, result_url, username, timestamp))  # 记录日志
        # 将日志写入文件
        with open("inference_log.txt", "a") as f:
            f.write(f"{log_id}, {result_url}, {username}, {timestamp}\n")

def read_log():
    logs = []
    if os.path.exists("inference_log.txt"):
        with open("inference_log.txt", "r") as f:
            logs = f.readlines()
    return logs

def log_page():
    # 日志页面
    st.title("推理日志记录")
    logs = read_log()
    log_data = [log.strip().split(', ') for log in logs]
    log_df = pd.DataFrame(log_data, columns=["Uuid", "Result URL", "Username", "Timestamp"])
    st.table(log_df)