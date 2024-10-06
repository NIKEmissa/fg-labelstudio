# logging.py

import os
import uuid
from datetime import datetime
from queue import Queue
import threading
import streamlit as st
import pandas as pd
import json

# 全局日志队列
log_queue = Queue()
lock = threading.Lock()

def log_inference(result_url, username, others=None):
    log_id = str(uuid.uuid4())  # 生成唯一的 UUID
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 获取当前时间戳
    
    # 将 others 字典转换为字符串
    others_str = ', '.join([f'"{key}": "{value}"' for key, value in (others or {}).items()]) if others else "{}"
    others_str = "{" + others_str + "}"  # 包装成字典格式字符串
    
    with lock:
        log_queue.put((log_id, result_url, username, timestamp, others_str))  # 记录日志
        # 将日志写入文件
        with open("inference_log.txt", "a") as f:
            f.write(f"{log_id}, {result_url}, {username}, {timestamp}, {others_str}\n")

import json

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
