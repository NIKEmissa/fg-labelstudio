import streamlit as st
from modules.authentication import user_login
from modules.dense_parse_csv import dense_parse_csv
from modules.streamlit_image_viewer import image_viewer



def main():
    # 设置页面配置为宽屏模式
    st.set_page_config(page_title="Label Studio Task Creator", layout="wide")

    st.sidebar.title("请选择功能")

    page = st.sidebar.selectbox("", ["工具-选图工具", "工具-选图CSV转成标注系统格式"])
    
    if page == "工具-选图CSV转成标注系统格式":
        dense_parse_csv() 
    elif page == "工具-选图工具":
        image_viewer()
            
if __name__ == "__main__":
    main()
