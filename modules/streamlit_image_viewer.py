import pandas as pd
from PIL import Image
import requests
from io import BytesIO
import streamlit as st
import pyperclip


def translate_list_eng(_source_list, df_trans, _source_filter_column):
    tgt_cn_list = {}

    for item in _source_list:
        if item == 'Indeterminate':
            continue

        conditions = (df_trans['标签分组'] == _source_filter_column) & (df_trans['英文.2'] == item)
        try:
            # print(df_trans[conditions]['标签'].iloc[0])
            tgt_cn_list[df_trans[conditions]['标签'].iloc[0]] = item
        except:
            # print(df_trans[conditions]['标签'], item)
            pass

    return tgt_cn_list

def get_unique_values(df, col):
    # 将选定列中的 NaN 去除，并确保是字符串格式
    # 使用 str.split(',') 将每个单元格分割，再用 explode 打平成一个 Series
    # 最后调用 str.strip() 去除可能的空白，并使用 pd.unique 得到唯一值
    unique_vals = pd.unique(
        df[col].dropna().astype(str)
              .str.split(',')
              .explode()
              .str.strip()
    )
    return unique_vals.tolist()

def filter_Unnamed_list(_source_list):
    # 假设 _source_list 是一个 pandas.Index 对象，进行处理
    return [col for col in _source_list if "Unnamed" not in col]

# Function to load image from URL with caching
@st.cache_resource
def load_image(image_url):
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        st.error(f"加载图片失败: {e}")
        return None

# Function to read DataFrame with caching
@st.cache_data
def load_dataframe(file_path):
    return pd.read_csv(file_path)

# Function to display images with pagination in n x n grid
def display_images_with_pagination(df, filter_column, filter_value, images_per_page=3):
    # Filter rows based on the specified column and value
    # filtered_df = df[df[filter_column] == filter_value]
    # filtered_df = filtered_df[filtered_df['category'] == '连衣裙']
    filtered_df = df[df[filter_column].str.contains(filter_value, na=False) & (df['category'] == '连衣裙')]
    
    
    if filtered_df.empty:
        st.write("没有符合条件的图片")
        return
    
    # Pagination logic
    total_images = len(filtered_df)
    total_pages = (total_images + images_per_page - 1) // images_per_page
    
    # Initialize current page in session state if not exists
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    
    # Streamlit slider for selecting page number
    page_slider = st.slider("选择页面", 1, total_pages, st.session_state.current_page)
    
    # Sync slider and input box
    if page_slider != st.session_state.current_page:
        st.session_state.current_page = page_slider
    
    # Left and right pagination buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("上一页", key=f"prev_page_{st.session_state.current_page}") and st.session_state.current_page > 1:
            st.session_state.current_page -= 1
    with col3:
        if st.button("下一页", key=f"next_page_{st.session_state.current_page}") and st.session_state.current_page < total_pages:
            st.session_state.current_page += 1
    
    # Display images for the current page
    start_idx = (st.session_state.current_page - 1) * images_per_page
    end_idx = min(start_idx + images_per_page, total_images)
    page_images = filtered_df.iloc[start_idx:end_idx]
    
    # Calculate number of rows and columns for the grid (n x n grid)
    n = int(images_per_page ** 0.5)  # Square grid (n x n)
    num_rows = (images_per_page + n - 1) // n  # Number of rows needed
    
    # Create a grid for displaying images
    for row_idx in range(num_rows):
        cols = st.columns(n)
        for col_idx in range(n):
            image_idx = row_idx * n + col_idx
            if image_idx < len(page_images):
                row = page_images.iloc[image_idx]
                with cols[col_idx]:
                    # Display the image
                    st.image(load_image(row['url']), caption=f"{row['url']}", use_container_width=True)
                    # # Add a button to copy the URL to clipboard
                    # if st.button(f"复制 {row['url']} 到剪贴板", key=f"copy_{image_idx}"):
                    #     pyperclip.copy(row['url'])  # Copy URL to clipboard
                    #     st.success(f"已复制: {row['url']}")  # Show success message
    
    # Show current page number
    st.write(f"当前页数: {st.session_state.current_page}/{total_pages}") 

# Streamlit App
def image_viewer():
    # 设置宽屏模式
    # st.set_page_config(layout="wide")
    
    # Load the DataFrame (only loads once when the app starts)
    if 'df' not in st.session_state:
        st.session_state.df = load_dataframe('/data1/code/dengxinzhe/sources/query_fg11-fg13_merged_20240605.csv')

    df = st.session_state.df

    # Load the DataFrame (only loads once when the app starts)
    if 'df_title_dict' not in st.session_state:
        st.session_state.df_title_dict = load_dataframe('/data1/code/dengxinzhe/sources/翻译推理 和 专家核验 记录表 - Title 映射表.csv')

    df_title_dict = st.session_state.df_title_dict

    # Load the DataFrame (only loads once when the app starts)
    if 'df_trans_dict' not in st.session_state:
        st.session_state.df_trans_dict = load_dataframe('/data1/code/dengxinzhe/fg-labelstudio/other_interesting/dense_caption/翻译推理 和 专家核验 记录表 - 数仓370个标签原表.csv')

    df_trans_dict = st.session_state.df_trans_dict    

    # Streamlit UI
    st.title("图片查看器")
    
    select_columns = filter_Unnamed_list(df_title_dict['中文'])

    # Select column and value for filtering
    filter_column_cn = st.selectbox("选择要过滤的列", select_columns)
    filter_column = df_title_dict[df_title_dict['中文'] == filter_column_cn].iloc[0]['转换后类别']

    rst = get_unique_values(df, filter_column)
    select_columns_value_cn = translate_list_eng(rst, df_trans_dict, filter_column_cn)
    filter_value_cn = st.selectbox(f"请输入要过滤的 {filter_column_cn} 的值", select_columns_value_cn.keys())
    filter_value = select_columns_value_cn[filter_value_cn]

    st.markdown(f"选择的要素项：{filter_column_cn}（{filter_column}）\n选择的要素值：{filter_value_cn}（{filter_value}）")

    # Select number of images per page
    images_per_page = st.selectbox("每页显示的图片数量", options=[3, 6, 9, 12, 24, 48], index=3)

    if filter_value:
        display_images_with_pagination(df, filter_column, filter_value, images_per_page)


import streamlit as st
import pandas as pd
import math

# 缓存数据加载，加快后续访问
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_feather(file_path)
        return df
    except Exception as e:
        st.error(f"读取 Feather 文件时发生错误: {e}")
        return None

def image_viewer_style():
    st.title("图片浏览")
    
    # 载入数据文件（假设文件中包含图片 URL，字段名为 'url'）
    file_path = "/data1/datasets/liujunfa/style/style_data.feather"
    df = load_data(file_path)
    if df is None:
        st.stop()
    
    if 'url' not in df.columns:
        st.error("数据中不存在 'url' 列，请检查数据格式。")
        st.stop()
    
    total_images = len(df)
    
    st.sidebar.header("设置")
    # 用户在侧边栏选择每页显示的图片数量
    per_page = st.sidebar.number_input("每页显示图片数量", min_value=1, max_value=total_images, value=9, step=1)
    
    total_pages = math.ceil(total_images / per_page)
    
    # 使用 session_state 保存当前页码，便于跨组件更新
    if "page" not in st.session_state:
        st.session_state["page"] = 1
    
    # 页码选择滑动条（和 session_state 绑定）
    page = st.slider("选择页码", 1, total_pages, value=st.session_state["page"], key="page_slider")
    st.session_state["page"] = page  # 更新当前页码
    
    # 上一页与下一页按钮布局
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("上一页"):
            if st.session_state["page"] > 1:
                st.session_state["page"] -= 1
                # 如果存在 experimental_rerun 则调用，否则不调用
                if hasattr(st, "experimental_rerun"):
                    st.experimental_rerun()
    with col3:
        if st.button("下一页"):
            if st.session_state["page"] < total_pages:
                st.session_state["page"] += 1
                if hasattr(st, "experimental_rerun"):
                    st.experimental_rerun()
    
    # 根据当前页码截取数据
    current_page = st.session_state["page"]
    start_idx = (current_page - 1) * per_page
    end_idx = start_idx + per_page
    current_df = df.iloc[start_idx:end_idx]
    
    # 计算网格每行的列数：采用 math.ceil(sqrt(每页图片数量))
    num_cols = math.ceil(math.sqrt(per_page))
    image_list = current_df['url'].tolist()
    
    st.write(f"当前显示第 {current_page} 页，共 {total_pages} 页，总图片数：{total_images}")
    
    # 按照网格排列展示图片及其 URL
    for i in range(0, len(image_list), num_cols):
        cols = st.columns(num_cols)
        for j, url in enumerate(image_list[i:i+num_cols]):
            with cols[j]:
                st.image(url, use_container_width=True)
                st.caption(url)
