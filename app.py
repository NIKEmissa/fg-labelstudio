import streamlit as st
from modules.authentication import user_login
from modules.logging import log_page
from modules.inference import run_inference, run_inference_independently
from modules.compare_flux_versions import flux_of_different_versions, flux_of_different_versions_text
from modules.image_to_text import image_to_text_compare
from modules.text_to_image import text_to_image_compare
from modules.test_components import test_page
from modules.flux_to_html import flux_to_html



def main():
    # 设置页面配置为宽屏模式
    st.set_page_config(page_title="Label Studio Task Creator", layout="wide")

    user_login()  # 登录模块

    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        page = st.sidebar.selectbox("选择页面", ["工具-提示词融合", "工具-文生图（多模型比较；图片维度）", "工具-文生图（多模型比较；文字维度）", "工具-文生图（单图校验）", "工具-图生文（单图校验）", "工具-Flux参数对比（生图效果）", "查看日志", "系统设置", "测试"])
        
        if page == "工具-提示词融合":
            run_inference_independently()  # 推理任务模块
        elif page == "工具-文生图（多模型比较；图片维度）":
            flux_of_different_versions()
        elif page == "工具-文生图（多模型比较；文字维度）":
            flux_of_different_versions_text()
        elif page == "工具-文生图（单图校验）":
            text_to_image_compare()            
        elif page == "工具-图生文（单图校验）":
            image_to_text_compare()            
        elif page == "工具-Flux参数对比（生图效果）":
            flux_to_html()
        elif page == "查看日志":
            log_page()  # 日志模块
        elif page == "系统设置":
            pass
        elif page == "测试":
            test_page()

if __name__ == "__main__":
    main()
