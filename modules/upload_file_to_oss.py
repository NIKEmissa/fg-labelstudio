import streamlit as st
import oss2
import os
import pandas as pd
from io import BytesIO
import logging
from datetime import datetime
import json

# 配置日志
logging.basicConfig(filename='upload_log.txt', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

# 读取用户配置信息
def load_user_config(config_path='user_config.json'):
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 读取OSS配置信息
def load_oss_config(oss_config_path='oss_config.json'):
    with open(oss_config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 用户登录验证
def authenticate(username, password, user_data):
    return username in user_data and user_data[username] == password

# 注销功能
def logout():
    st.session_state['authenticated'] = False
    st.session_state.pop('username', None)
    st.sidebar.success('已成功登出！')

# 下载按钮封装为独立组件
@st.fragment
def download_csv(results_df):
    st.download_button(
        label="下载图片URL结果CSV",
        data=results_df.to_csv(index=False).encode('utf-8'),
        file_name='image_urls.csv',
        mime='text/csv',
        key='download_results_csv'
    )

# 主页面函数
def upload_page():
    st.title('🌐 获取图片URL')

    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    st.sidebar.header("用户登录")

    if not st.session_state['authenticated']:
        username_input = st.sidebar.text_input('用户名')
        password_input = st.sidebar.text_input('密码', type='password')

        if st.sidebar.button('登录'):
            user_data = load_user_config()
            if authenticate(username_input, password_input, user_data):
                st.session_state['authenticated'] = True
                st.session_state['username'] = username_input
                st.sidebar.success(f'登录成功，欢迎 {username_input}！')
                st.rerun()
            else:
                st.sidebar.error('用户名或密码错误！')

        st.warning('请登录以使用功能。')
        return

    else:
        st.sidebar.success(f'已登录: {st.session_state.get("username", "")}', icon="✅")
        if st.sidebar.button('登出'):
            logout()
            st.rerun()

        oss_config = load_oss_config()
        selected_files = st.file_uploader("请选择本地图片文件（支持多选）", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

        if st.button('开始获取URL'):
            results_df = upload_file_to_oss(oss_config, selected_files, st.session_state['username'])
            if results_df is not None:
                download_csv(results_df)

@st.fragment
def upload_file_to_oss(oss_config, selected_files, username):
    if not selected_files:
        st.error('请至少选择一个图片文件')
        return None

    try:
        auth = oss2.Auth(oss_config['access_key_id'], oss_config['access_key_secret'])
        bucket = oss2.Bucket(auth, oss_config['endpoint'], oss_config['bucket_name'])

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        oss_dir = f"ai_images/xd2/Downloads/images/dense_annotation_expert_select/{username}/{timestamp}/"

        uploaded_data = []
        successful_count = 0
        for file in selected_files:
            oss_key = os.path.join(oss_dir, file.name)
            upload_start_time = datetime.now()
            file.seek(0)
            file_content = file.read()

            exists = False
            try:
                oss_file_info = bucket.head_object(oss_key)
                if oss_file_info.content_length == len(file_content):
                    exists = True
                    msg = f'图片已存在，跳过：{file.name}'
                    st.info(msg)
                    logging.info(msg)
            except oss2.exceptions.NoSuchKey:
                pass

            if not exists:
                bucket.put_object(oss_key, BytesIO(file_content))
                upload_end_time = datetime.now()
                msg = f'获取URL成功：{file.name}'
                st.success(msg)
                logging.info(f"用户名: {username}, 图片名称: {file.name}, 存储路径: {oss_key}, 开始时间: {upload_start_time}, 完成时间: {upload_end_time}, 状态: 成功")
                successful_count += 1
            else:
                upload_end_time = datetime.now()
                logging.info(f"用户名: {username}, 图片名称: {file.name}, 存储路径: {oss_key}, 开始时间: {upload_start_time}, 完成时间: {upload_end_time}, 状态: 已存在跳过")

            oss_url = f'https://{oss_config["bucket_name"]}.{oss_config["endpoint"]}/{oss_key}'
            uploaded_data.append({'图片名称': file.name, '图片URL': oss_url})

        st.success(f'处理完成！成功处理 {successful_count}/{len(selected_files)} 个文件')

        return pd.DataFrame(uploaded_data)

    except Exception as e:
        error_msg = f'处理过程中出错：{e}'
        st.error(error_msg)
        logging.error(error_msg)
        return None