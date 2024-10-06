# inference.py

import streamlit as st
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from pprint import pprint
from utils.ai_tools import gpt
from modules.logging import log_inference
from utils.parser import get_base_prompt, get_merge_prompt
from utils.label_tools import abc, load_config, format_string_for_xml, count_tokens, LabelStudioManager, convert_to_html_and_escape_xml, get_column_index
from utils.utils import save_uploaded_file

config_path = "./config/prompts.py"
BASE_PROMPT = get_base_prompt(config_path)
MERGE_PROMPT = get_merge_prompt(config_path)
# 加载配置
label_config = load_config()
pprint(label_config)
pprint(label_config)

def image_to_text_compare():
    # Streamlit 页面配置
    st.title("'图生文' 标注创建器")
    label_config['labelstudio']['url'] = 'http://localhost:20003'
    label_config['labelstudio']['external_port'] = '20003'

    # 用户上传 CSV 文件
    st.header("第一步：上传CSV文件")
    uploaded_file = st.file_uploader("Upload your CSV file here", type="csv")
    
    # 后台创建labelstudio manager
    label_manager = LabelStudioManager(label_config)    

    if uploaded_file is not None:
        # 保存上传的 CSV 文件
        csv_path = save_uploaded_file(uploaded_file)  # 保存文件
        
        # 解析 CSV 文件
        df = pd.read_csv(uploaded_file)
        
        column_names = df.columns.tolist()

        # 并排显示选择功能
        st.header("第二步：指定处理内容")    
        col1, col2, col3 = st.columns(3)

        with col1:
            original_image_col = st.selectbox("Original Image URL", options=column_names, index=get_column_index(df, 'url'))

        with col2:
            all_prompt_cn_col = st.selectbox("Chinese All_prompt", options=column_names, index=get_column_index(df, 'All_prompts_cn'))

        with col3:
            all_prompt_en_col = st.selectbox("English All_prompt", options=column_names, index=get_column_index(df, 'All_prompts'))
            
        # 添加滑动选择器
        start_row, end_row = st.slider(
            "Select range of rows to upload",
            min_value=0,
            max_value=len(df) - 1,
            value=(0, len(df) - 1)
        )            

        # 选择的 DataFrame 范围
        column_names = [original_image_col, all_prompt_cn_col, all_prompt_en_col]
        selected_df = df.iloc[start_row:end_row+1][column_names]
        
        # 实时显示选定的 DataFrame
        st.header("第三步：核验表格&启动")
        st.dataframe(selected_df)
        
        # 运行按钮
        if st.button("启动"):

            # 模拟运行进度条
            with st.spinner('运行中...'):
                progress_bar = st.progress(0)
                total_rows = len(selected_df)
                results = []

                st.text(f"正在初始化项目...")

                project = label_manager.create_project(title='图生文', task_type='image_to_text_compare')
                project_url = label_manager.get_project_data_url(project)

                st.markdown(f"项目初始化完毕 [项目链接]({project_url})")

                for index, (_, row) in enumerate(tqdm(selected_df.iterrows(), total=total_rows)):

                    task_data = {
                        'data': {
                            'url': convert_to_html_and_escape_xml(row[original_image_col]),
                            'All_prompts': convert_to_html_and_escape_xml(row[all_prompt_cn_col]),
                        }
                    }            

                    print(task_data)
                    
                    success = label_manager.upload_task(project, task_data)
                    if success:
                        print(f"Task {index} uploaded successfully.")
                    else:
                        print(f"Failed to upload Task {index}.")

                    # 更新进度条和文字进度
                    progress = min((index + 1) / total_rows, 1.0)
                    progress_bar.progress(progress)
                    st.text(f"当前进度: {index + 1} / {total_rows} ({progress:.1%}) 上传打标结果 {'成功' if success else '失败'}")
                
                # 获取当前用户名
                current_username = st.session_state["username"]
                
                # 记录日志，包括上传的 CSV 路径、start_row 和 end_row
                log_data = {
                    "csv_path": csv_path,
                    "start_row": start_row,
                    "end_row": end_row
                }
                
                log_inference(project_url, current_username, log_data)  # 记录日志

                st.success('运行完成！')
                st.markdown(f'请打开 [结果链接]({project_url})')
                # st.markdown("CSV 已保存为 output.csv")                