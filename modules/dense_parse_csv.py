import streamlit as st
import pandas as pd
import json
import datetime

def process_csv_data(df, filter_labels=None):
    """
    根据 CSV 数据和过滤条件生成目标 JSON 数据
    """
    target_list = []
    for index, row in df.iterrows():
        if filter_labels and row.get('标签值') not in filter_labels:
            continue
        if pd.isna(row.get('URL')):
            continue
        sub_dict = {
            'id': str(index),
            'pictureList': [
                {
                    'id': index,
                    'url': row.get('URL')
                }
            ]
        }
        target_list.append(sub_dict)
    return target_list

@st.fragment()
def render_filter_and_generate(df, csv_filename):
    """
    封装过滤控件与生成 JSON 按钮的逻辑，
    用户点击“生成 JSON”后直接触发数据格式转换并显示下载按钮
    """
    # 启用过滤选项
    filter_enabled = st.checkbox("启用标签值过滤", value=True, key="filter_enabled")
    filter_labels = None
    if filter_enabled:
        unique_labels = sorted(df['标签值'].dropna().unique())
        filter_labels = st.multiselect("请选择要过滤的标签值", unique_labels, default=unique_labels, key="filter_labels")
    
    # 点击生成 JSON 按钮后直接执行数据转换并显示下载按钮
    if st.button("生成 JSON", key="generate_json"):
        result_data = process_csv_data(df, filter_labels if filter_enabled else None)
        valid_count = len(result_data)
        json_str = json.dumps(result_data, ensure_ascii=False, indent=2)
        
        # 构造下载文件名：result_{csv_name}_{timestamp}.txt，空格替换为下划线
        csv_name = csv_filename.replace(" ", "_")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"result_{csv_name}_{timestamp}.txt"
        
        st.success(f"有效数据量：{valid_count} 条记录")
        st.download_button(
            label="下载 TXT 文件",
            data=json_str,
            file_name=file_name,
            mime="text/plain"
        )

def dense_parse_csv():
    st.title("CSV 到 TXT 转换工具")
    st.write("上传 CSV 文件，并可选按【标签值】进行过滤，生成符合需求的 TXT 数据。")
    
    uploaded_file = st.file_uploader("请选择 CSV 文件", type="csv")
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"读取 CSV 文件失败：{e}")
            return
        
        csv_filename = uploaded_file.name
        render_filter_and_generate(df, csv_filename)

if __name__ == '__main__':
    dense_parse_csv()
