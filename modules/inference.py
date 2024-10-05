# inference.py

import streamlit as st
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from utils.ai_tools import gpt
from modules.logging import log_inference
from utils.parser import get_base_prompt, get_merge_prompt
from utils.label_tools import abc, load_config, format_string_for_xml, count_tokens, LabelStudioManager, convert_to_html_and_escape_xml, get_column_index

config_path = "/data1/A800-01/data/xinzhedeng/MyCode/Project/labelstudio/config/prompts.py"
config_path = "./config/prompts.py"
BASE_PROMPT = get_base_prompt(config_path)
MERGE_PROMPT = get_merge_prompt(config_path)
# 加载配置
label_config = load_config()

def calculate_height(text):
    lines = text.split('\n')
    return max(200, len(lines) * 20)  # 初始高度为 200，后续根据行数动态调整

def run_inference():
    # Streamlit 页面配置
    st.title("Label Studio Task Creator")
    st.write("上传 CSV 文件，并输入 prompt1 和 prompt2")

    # 用户上传 CSV 文件
    uploaded_file = st.file_uploader("上传 CSV 文件", type="csv")

    # 并排的两个用户输入窗口
    col1, col2 = st.columns(2)
    area_height = max(calculate_height(BASE_PROMPT), calculate_height(MERGE_PROMPT))
    with col1:
        base_prompt = st.text_area("base_prompt", value=BASE_PROMPT, height=area_height)
    with col2:
        merge_prompt = st.text_area("merge_prompt", value=MERGE_PROMPT, height=area_height)

    # 运行按钮
    if st.button("运行"):
        if uploaded_file is not None:
            # 读取 CSV 文件
            df = pd.read_csv(uploaded_file)
            st.write("CSV 文件内容：")
            st.write(df)

            # 添加新列，如果它们不存在
            for column in ['image_caption_en', 'image_caption_cn', 'all_others_en', 'all_others_cn', 
                           'merged_caption_en', 'merged_caption_cn', 'base_prompt', 'merge_prompt']:
                if column not in df.columns:
                    df[column] = ""

            # 模拟运行进度条
            with st.spinner('运行中...'):
                progress_bar = st.progress(0)
                total_rows = len(df)
                results = []

                for index, row in tqdm(df.iterrows(), total=total_rows):
                    rst = gpt(row['url'], row['all_others'], BASE_PROMPT, MERGE_PROMPT)

                    # 存储结果到 DataFrame
                    results.append({
                        'image_caption_en': rst['image_caption_en'],
                        'image_caption_cn': rst['image_caption_cn'],
                        'all_others_en': rst['all_others_en'],
                        'all_others_cn': rst['all_others_cn'],
                        'merged_caption_en': rst['merged_caption_en'],
                        'merged_caption_cn': rst['merged_caption_cn'],
                        'base_prompt': BASE_PROMPT,
                        'merge_prompt': MERGE_PROMPT
                    })

                    # 更新进度条和文字进度
                    progress = (index + 1) / total_rows
                    progress_bar.progress(progress)
                    st.text(f"当前进度: {index + 1} / {total_rows} ({progress:.1%})")

            # 更新 DataFrame
            for i, result in enumerate(results):
                for key, value in result.items():
                    df.at[i, key] = value

            # 保存修改后的 DataFrame 到本地 CSV
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df.to_csv(f"output2_test_{timestamp}.csv", index=False)

            # 调用接口
            result_url = abc(label_config, df)

            # 获取当前用户名
            current_username = st.session_state["username"]
            log_inference(result_url, current_username)  # 记录日志

            st.success('运行完成！')
            st.markdown(f'请打开 [结果链接]({result_url})')
            st.markdown("CSV 已保存为 output.csv")
        else:
            st.error("请先上传 CSV 文件。")
            
            
def run_inference_independently():
    # Streamlit 页面配置
    st.title("'提示词融合' 标注创建器")
    st.write("上传 CSV 文件，并输入 base_prompt 和 merge_prompt")
    label_config['labelstudio']['url'] = 'http://localhost:20003'
    label_config['labelstudio']['external_port'] = '20003'    

    # 用户上传 CSV 文件
    uploaded_file = st.file_uploader("上传 CSV 文件", type="csv")
    
    # 后台创建labelstudio manager
    label_manager = LabelStudioManager(label_config)

    # 并排的两个用户输入窗口
    col1, col2 = st.columns(2)
    area_height = max(calculate_height(BASE_PROMPT), calculate_height(MERGE_PROMPT))
    with col1:
        base_prompt = st.text_area("base_prompt", value=BASE_PROMPT, height=area_height)
    with col2:
        merge_prompt = st.text_area("merge_prompt", value=MERGE_PROMPT, height=area_height)

    # 运行按钮
    if st.button("运行"):
        if uploaded_file is not None:
            # 读取 CSV 文件
            df = pd.read_csv(uploaded_file)
            st.write("CSV 文件内容：")
            st.write(df)

            # 添加新列，如果它们不存在
            for column in ['image_caption_en', 'image_caption_cn', 'all_others_en', 'all_others_cn', 
                           'merged_caption_en', 'merged_caption_cn', 'base_prompt', 'merge_prompt']:
                if column not in df.columns:
                    df[column] = ""

            # 模拟运行进度条
            with st.spinner('运行中...'):
                progress_bar = st.progress(0)
                total_rows = len(df)
                results = []
                
                st.text(f"正在初始化项目...")
                
                project = label_manager.create_project(title='提示词融合')
                project_url = label_manager.get_project_data_url(project)

                st.markdown(f"项目初始化完毕 [项目链接]({project_url})")

                for index, row in tqdm(df.iterrows(), total=total_rows):
                    retry = True
                    retry_cnt = 0
                    while retry and retry_cnt <= label_config['inference']['max_retry']:
                        rst = gpt(row['url'], row['all_others'], base_prompt, merge_prompt)
                        retry_cnt += 1     
                        
                        retry = rst['merged_caption_cn'] is None
                        
                        if retry:
                            st.markdown(f"咦 gpt 打标出问题了，可能是 api 异常。让我重试下（{retry_cnt}/{label_config['inference']['max_retry']}）")

                    # 存储结果到 DataFrame
                    results.append({
                        'image_caption_en': rst['image_caption_en'],
                        'image_caption_cn': rst['image_caption_cn'],
                        'all_others_en': rst['all_others_en'],
                        'all_others_cn': rst['all_others_cn'],
                        'merged_caption_en': rst['merged_caption_en'],
                        'merged_caption_cn': rst['merged_caption_cn'],
                        'base_prompt': BASE_PROMPT,
                        'merge_prompt': MERGE_PROMPT
                    })
                    
                    task_data = {
                        'data': {
                            'OriginalImage': row['url'],
                            'Baseline': convert_to_html_and_escape_xml(rst['image_caption_cn']),
                            'Baseline_token_cnt': str(count_tokens(format_string_for_xml(rst['image_caption_cn']))),
                            'Baseline_EN': convert_to_html_and_escape_xml(rst['image_caption_en']),
                            'Baseline_EN_token_cnt': str(count_tokens(format_string_for_xml(rst['image_caption_en']))),
                            'All_Others': convert_to_html_and_escape_xml(rst['all_others_cn']),
                            'All_Others_token_cnt': str(count_tokens(format_string_for_xml(rst['all_others_cn']))),
                            'All_Others_EN': convert_to_html_and_escape_xml(rst['all_others_en']),
                            'All_Others_EN_token_cnt': str(count_tokens(format_string_for_xml(rst['all_others_en']))),
                            'Merged_Description': convert_to_html_and_escape_xml(rst['merged_caption_cn']),
                            'Merged_Description_token_cnt': str(count_tokens(format_string_for_xml(rst['merged_caption_cn']))),
                            'Merged_Description_EN': convert_to_html_and_escape_xml(rst['merged_caption_en']),
                            'Merged_Description_EN_token_cnt': str(count_tokens(convert_to_html_and_escape_xml(rst['merged_caption_en'])))
                        }
                    }
                    print(f"<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>")
                    print(convert_to_html_and_escape_xml(rst['merged_caption_en']))
                    print(str(count_tokens(convert_to_html_and_escape_xml(row['merged_caption_en']))))
                    print(f"<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>")
                    
                    success = label_manager.upload_task(project, task_data)
                    if success:
                        print(f"Task {index} uploaded successfully.")
                    else:
                        print(f"Failed to upload Task {index}.")

                    # 更新进度条和文字进度
                    progress = (index + 1) / total_rows
                    progress_bar.progress(progress)
                    st.text(f"当前进度: {index + 1} / {total_rows} ({progress:.1%}) 上传打标结果 {'成功' if success else '失败'}")

            # 更新 DataFrame
            for i, result in enumerate(results):
                for key, value in result.items():
                    df.at[i, key] = value

            # 保存修改后的 DataFrame 到本地 CSV
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df.to_csv(f"output2_test_{timestamp}.csv", index=False)

            # # 调用接口
            # result_url = abc(label_config, df)

            # 获取当前用户名
            current_username = st.session_state["username"]
            log_inference(project_url, current_username)  # 记录日志

            st.success('运行完成！')
            st.markdown(f'请打开 [结果链接]({project_url})')
            st.markdown("CSV 已保存为 output.csv")
        else:
            st.error("请先上传 CSV 文件。")
