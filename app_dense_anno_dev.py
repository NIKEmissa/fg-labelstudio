import streamlit as st
from modules.authentication import user_login
from modules.dense_parse_csv import dense_parse_csv
from modules.streamlit_image_viewer import image_viewer
from modules.compare_anno_results import compare_anno_results



def main():
    # 设置页面配置为宽屏模式
    st.set_page_config(page_title="Label Studio Task Creator", layout="wide")

    st.sidebar.title("请选择功能")

    page = st.sidebar.selectbox("选项", ["工具-选图工具", "工具-选图CSV转成标注系统格式", "工具-对比标注结果", "工具-对比标注整体分析"])
    
    if page == "工具-选图CSV转成标注系统格式":
        dense_parse_csv() 
    elif page == "工具-选图工具":
        image_viewer()
    elif page == "工具-对比标注结果":
        compare_anno_results()
    elif page == "工具-对比标注整体分析":
        compare_anno_results()

if __name__ == "__main__":
    main()
