import streamlit as st
st.set_page_config(page_title="Label Studio Task Creator", layout="wide")

import datetime
import threading
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
import pyperclip
import math
import tempfile
import os
import pyarrow.feather as feather

# -------------------------------
# 自检日志与健康检查函数
# -------------------------------
def log_self_check(stage, status, message):
    """
    自检日志函数，格式为：
    [SelfCheck] [时间戳] <模块名称> - <状态>: <消息>
    """
    timestamp = datetime.datetime.now().isoformat()
    print(f"[SelfCheck] [{timestamp}] {stage} - {status}: {message}")

# 各模块健康检查：各自调用对应模块的功能，不影响主流程

def health_check_translate_list_eng():
    try:
        dummy_source = ["hello", "world", "Indeterminate"]
        dummy_df_trans = pd.DataFrame({
            "标签分组": ["greeting", "greeting"],
            "英文.2": ["hello", "world"],
            "标签": ["你好", "世界"]
        })
        result = translate_list_eng(dummy_source, dummy_df_trans, "greeting")
        log_self_check("health_check_translate_list_eng", "PASS", f"Result: {result}")
    except Exception as e:
        log_self_check("health_check_translate_list_eng", "FAIL", f"Error: {e}")

def health_check_get_unique_values():
    try:
        dummy_df = pd.DataFrame({"col": ["a,b", "c", None]})
        result = get_unique_values(dummy_df, "col")
        log_self_check("health_check_get_unique_values", "PASS", f"Result: {result}")
    except Exception as e:
        log_self_check("health_check_get_unique_values", "FAIL", f"Error: {e}")

def health_check_load_image():
    try:
        # 使用一个常见的图片 URL 进行测试
        test_url = "https://www.baidu.com/img/bd_logo1.png"
        img = load_image(test_url)
        if img:
            log_self_check("health_check_load_image", "PASS", "Image loaded successfully")
        else:
            log_self_check("health_check_load_image", "FAIL", "Image is None")
    except Exception as e:
        log_self_check("health_check_load_image", "FAIL", f"Error: {e}")

def health_check_load_dataframe():
    try:
        dummy_df = pd.DataFrame({"a": [1, 2, 3]})
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=False) as tmp:
            dummy_file = tmp.name
            dummy_df.to_csv(tmp, index=False)
        loaded_df = load_dataframe(dummy_file)
        os.remove(dummy_file)
        if loaded_df is not None and loaded_df.equals(dummy_df):
            log_self_check("health_check_load_dataframe", "PASS", "DataFrame loaded successfully")
        else:
            log_self_check("health_check_load_dataframe", "FAIL", "DataFrame mismatch")
    except Exception as e:
        log_self_check("health_check_load_dataframe", "FAIL", f"Error: {e}")

def health_check_load_data():
    try:
        dummy_df = pd.DataFrame({"a": [1, 2, 3]})
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".feather", delete=False) as tmp:
            dummy_file = tmp.name
        feather.write_feather(dummy_df, dummy_file)
        loaded_df = load_data(dummy_file)
        os.remove(dummy_file)
        if loaded_df is not None and loaded_df.equals(dummy_df):
            log_self_check("health_check_load_data", "PASS", "Feather DataFrame loaded successfully")
        else:
            log_self_check("health_check_load_data", "FAIL", "Feather DataFrame mismatch")
    except Exception as e:
        log_self_check("health_check_load_data", "FAIL", f"Error: {e}")

def periodic_self_check():
    """
    定时自检函数，每 60 秒自动调用一次。该函数调用各模块健康检查函数，
    检查结果以统一格式打印到 terminal，不会干扰 Streamlit 主流程。
    """
    log_self_check("PeriodicSelfCheck", "START", "定时自检开始")
    health_check_translate_list_eng()
    health_check_get_unique_values()
    health_check_load_image()
    health_check_load_dataframe()
    health_check_load_data()
    log_self_check("PeriodicSelfCheck", "PASS", "定时自检完成")
    # 60秒后再次执行定时自检
    threading.Timer(60, periodic_self_check).start()

# -------------------------------
# 基础功能函数
# -------------------------------
def translate_list_eng(_source_list, df_trans, _source_filter_column):
    log_self_check("translate_list_eng", "START", "开始翻译列表")
    tgt_cn_list = {}
    for item in _source_list:
        if item == 'Indeterminate':
            continue
        conditions = (df_trans['标签分组'] == _source_filter_column) & (df_trans['英文.2'] == item)
        try:
            label = df_trans[conditions]['标签'].iloc[0]
            tgt_cn_list[label] = item
            log_self_check("translate_list_eng", "CHECK", f"'{item}' 翻译为 '{label}'")
        except Exception as e:
            log_self_check("translate_list_eng", "ERROR", f"翻译 '{item}' 时出错: {e}")
            pass
    log_self_check("translate_list_eng", "PASS", "列表翻译完成")
    return tgt_cn_list

def get_unique_values(df, col):
    log_self_check("get_unique_values", "START", f"开始提取 '{col}' 列的唯一值")
    unique_vals = pd.unique(
        df[col].dropna().astype(str)
              .str.split(',')
              .explode()
              .str.strip()
    )
    log_self_check("get_unique_values", "PASS", f"提取到 {len(unique_vals)} 个唯一值")
    return unique_vals.tolist()

def filter_Unnamed_list(_source_list):
    log_self_check("filter_Unnamed_list", "START", "开始过滤 Unnamed 列")
    filtered = [col for col in _source_list if "Unnamed" not in col]
    log_self_check("filter_Unnamed_list", "PASS", f"过滤后剩余 {len(filtered)} 列")
    return filtered

# -------------------------------
# 图片及数据加载函数
# -------------------------------
@st.cache_resource
def load_image(image_url):
    log_self_check("load_image", "START", f"从 URL 加载图片: {image_url}")
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        log_self_check("load_image", "PASS", "图片加载成功")
        return img
    except Exception as e:
        log_self_check("load_image", "FAIL", f"加载图片失败: {e}")
        st.error(f"加载图片失败: {e}")
        return None

@st.cache_data
def load_dataframe(file_path):
    log_self_check("load_dataframe", "START", f"从文件加载 CSV: {file_path}")
    try:
        df = pd.read_csv(file_path)
        log_self_check("load_dataframe", "PASS", f"DataFrame 加载成功，形状为 {df.shape}")
        return df
    except Exception as e:
        log_self_check("load_dataframe", "FAIL", f"加载 CSV 失败: {e}")
        st.error(f"加载 CSV 失败: {e}")
        return None

# -------------------------------
# 分页显示图片函数
# -------------------------------
def display_images_with_pagination(df, filter_column, filter_value, images_per_page=3):
    log_self_check("display_images_with_pagination", "START", "开始图片分页显示")
    # 根据过滤条件和类别过滤数据（此处示例过滤类别为“连衣裙”）
    filtered_df = df[df[filter_column].str.contains(filter_value, na=False) & (df['category'] == '连衣裙')]
    if filtered_df.empty:
        log_self_check("display_images_with_pagination", "WARN", "过滤后未找到符合条件的图片")
        st.write("没有符合条件的图片")
        return
    log_self_check("display_images_with_pagination", "CHECK", f"过滤后共 {len(filtered_df)} 张图片")
    total_images = len(filtered_df)
    total_pages = (total_images + images_per_page - 1) // images_per_page
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    page_slider = st.slider("选择页面", 1, total_pages, st.session_state.current_page)
    if page_slider != st.session_state.current_page:
        st.session_state.current_page = page_slider
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("上一页", key=f"prev_page_{st.session_state.current_page}") and st.session_state.current_page > 1:
            st.session_state.current_page -= 1
    with col3:
        if st.button("下一页", key=f"next_page_{st.session_state.current_page}") and st.session_state.current_page < total_pages:
            st.session_state.current_page += 1
    start_idx = (st.session_state.current_page - 1) * images_per_page
    end_idx = min(start_idx + images_per_page, total_images)
    page_images = filtered_df.iloc[start_idx:end_idx]
    n = int(images_per_page ** 0.5)
    num_rows = (images_per_page + n - 1) // n
    log_self_check("display_images_with_pagination", "CHECK", f"当前页 {st.session_state.current_page}/{total_pages}, 显示图片索引 {start_idx} 到 {end_idx}")
    for row_idx in range(num_rows):
        cols = st.columns(n)
        for col_idx in range(n):
            image_idx = row_idx * n + col_idx
            if image_idx < len(page_images):
                row = page_images.iloc[image_idx]
                with cols[col_idx]:
                    st.image(load_image(row['url']), caption=f"{row['url']}", use_container_width=True)
    st.write(f"当前页数: {st.session_state.current_page}/{total_pages}")
    log_self_check("display_images_with_pagination", "PASS", "图片分页显示完成")

# -------------------------------
# 主应用函数：图片查看器
# -------------------------------
def image_viewer():
    log_self_check("image_viewer", "START", "启动图片查看器")
    if 'df' not in st.session_state:
        st.session_state.df = load_dataframe('/data1/code/dengxinzhe/sources/query_fg11-fg13_merged_20240605.csv')
        if st.session_state.df is None:
            log_self_check("image_viewer", "FAIL", "df 加载失败")
            st.stop()
        log_self_check("image_viewer", "CHECK", "df 加载成功")
    else:
        log_self_check("image_viewer", "CHECK", "使用缓存中的 df")
    df = st.session_state.df
    if 'df_title_dict' not in st.session_state:
        st.session_state.df_title_dict = load_dataframe('/data1/code/dengxinzhe/sources/翻译推理 和 专家核验 记录表 - Title 映射表.csv')
        if st.session_state.df_title_dict is None:
            log_self_check("image_viewer", "FAIL", "df_title_dict 加载失败")
            st.stop()
        log_self_check("image_viewer", "CHECK", "df_title_dict 加载成功")
    else:
        log_self_check("image_viewer", "CHECK", "使用缓存中的 df_title_dict")
    df_title_dict = st.session_state.df_title_dict
    if 'df_trans_dict' not in st.session_state:
        st.session_state.df_trans_dict = load_dataframe('/data1/code/dengxinzhe/fg-labelstudio/other_interesting/dense_caption/翻译推理 和 专家核验 记录表 - 数仓370个标签原表.csv')
        if st.session_state.df_trans_dict is None:
            log_self_check("image_viewer", "FAIL", "df_trans_dict 加载失败")
            st.stop()
        log_self_check("image_viewer", "CHECK", "df_trans_dict 加载成功")
    else:
        log_self_check("image_viewer", "CHECK", "使用缓存中的 df_trans_dict")
    df_trans_dict = st.session_state.df_trans_dict    
    st.title("图片查看器")
    select_columns = filter_Unnamed_list(df_title_dict['中文'])
    filter_column_cn = st.selectbox("选择要过滤的列", select_columns)
    filter_column = df_title_dict[df_title_dict['中文'] == filter_column_cn].iloc[0]['转换后类别']
    rst = get_unique_values(df, filter_column)
    select_columns_value_cn = translate_list_eng(rst, df_trans_dict, filter_column_cn)
    filter_value_cn = st.selectbox(f"请输入要过滤的 {filter_column_cn} 的值", list(select_columns_value_cn.keys()))
    filter_value = select_columns_value_cn[filter_value_cn]
    st.markdown(f"选择的要素项：{filter_column_cn}（{filter_column}）\n选择的要素值：{filter_value_cn}（{filter_value}）")
    log_self_check("image_viewer", "CHECK", f"过滤条件设置：{filter_column} 包含 {filter_value}")
    images_per_page = st.selectbox("每页显示的图片数量", options=[3, 6, 9, 12, 24, 48], index=3)
    if filter_value:
        display_images_with_pagination(df, filter_column, filter_value, images_per_page)
    log_self_check("image_viewer", "PASS", "图片查看器运行完成")

# -------------------------------
# 第二部分：图片浏览（样式）
# -------------------------------
@st.cache_data
def load_data(file_path):
    log_self_check("load_data", "START", f"加载 Feather 文件: {file_path}")
    try:
        df = pd.read_feather(file_path)
        log_self_check("load_data", "PASS", f"Feather 数据加载成功，形状为 {df.shape}")
        return df
    except Exception as e:
        log_self_check("load_data", "FAIL", f"读取 Feather 文件时发生错误: {e}")
        st.error(f"读取 Feather 文件时发生错误: {e}")
        return None

def image_viewer_style():
    log_self_check("image_viewer_style", "START", "启动图片浏览（样式）")
    st.title("图片浏览")
    file_path = "/data1/datasets/liujunfa/style/style_data.feather"
    df = load_data(file_path)
    if df is None:
        log_self_check("image_viewer_style", "FAIL", "数据加载失败")
        st.stop()
    if 'url' not in df.columns:
        log_self_check("image_viewer_style", "FAIL", "数据中不存在 'url' 列")
        st.error("数据中不存在 'url' 列，请检查数据格式。")
        st.stop()
    log_self_check("image_viewer_style", "CHECK", "'url' 列存在，数据格式正确")
    total_images = len(df)
    st.sidebar.header("设置")
    per_page = st.sidebar.number_input("每页显示图片数量", min_value=1, max_value=total_images, value=9, step=1)
    total_pages = math.ceil(total_images / per_page)
    if "page" not in st.session_state:
        st.session_state["page"] = 1
    page = st.slider("选择页码", 1, total_pages, value=st.session_state["page"], key="page_slider")
    st.session_state["page"] = page
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("上一页"):
            if st.session_state["page"] > 1:
                st.session_state["page"] -= 1
                if hasattr(st, "experimental_rerun"):
                    st.experimental_rerun()
    with col3:
        if st.button("下一页"):
            if st.session_state["page"] < total_pages:
                st.session_state["page"] += 1
                if hasattr(st, "experimental_rerun"):
                    st.experimental_rerun()
    current_page = st.session_state["page"]
    start_idx = (current_page - 1) * per_page
    end_idx = start_idx + per_page
    current_df = df.iloc[start_idx:end_idx]
    num_cols = math.ceil(math.sqrt(per_page))
    image_list = current_df['url'].tolist()
    st.write(f"当前显示第 {current_page} 页，共 {total_pages} 页，总图片数：{total_images}")
    log_self_check("image_viewer_style", "CHECK", f"当前页: {current_page}/{total_pages}, 显示图片数量: {len(image_list)}")
    for i in range(0, len(image_list), num_cols):
        cols = st.columns(num_cols)
        for j, url in enumerate(image_list[i:i+num_cols]):
            with cols[j]:
                st.image(url, use_container_width=True)
                st.caption(url)
    log_self_check("image_viewer_style", "PASS", "图片浏览（样式）显示完成")

# -------------------------------
# 启动定时自检（确保只启动一次）
# -------------------------------
if "periodic_self_check_started" not in st.session_state:
    st.session_state["periodic_self_check_started"] = True
    periodic_self_check()

# -------------------------------
# 根据需要选择运行哪个页面
# -------------------------------
if __name__ == "__main__":
    st.sidebar.title("导航")
    page = st.sidebar.radio("选择页面", ("图片查看器", "图片浏览（样式）"))
    if page == "图片查看器":
        image_viewer()
    else:
        image_viewer_style()
