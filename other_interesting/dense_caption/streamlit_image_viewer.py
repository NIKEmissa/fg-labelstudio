import pandas as pd
from PIL import Image
import requests
from io import BytesIO
import streamlit as st
import pyperclip

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
    filtered_df = df[df[filter_column] == filter_value]
    filtered_df = filtered_df[filtered_df['category'] == '连衣裙']
    
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
                    st.image(load_image(row['url']), caption=f"图片 URL: {row['url']}", use_container_width=True)
                    # Add a button to copy the URL to clipboard
                    if st.button(f"复制 {row['url']} 到剪贴板", key=f"copy_{image_idx}"):
                        pyperclip.copy(row['url'])  # Copy URL to clipboard
                        st.success(f"已复制: {row['url']}")  # Show success message
    
    # Show current page number
    st.write(f"当前页数: {st.session_state.current_page}/{total_pages}") 

# Streamlit App
def main():
    # Load the DataFrame (only loads once when the app starts)
    if 'df' not in st.session_state:
        st.session_state.df = load_dataframe('/data1/code/dengxinzhe/sources/query_fg11-fg13_merged_20240605.csv')

    df = st.session_state.df

    # Streamlit UI
    st.title("图片查看器")
    
    # Select column and value for filtering
    filter_column = st.selectbox("选择要过滤的列", df.columns)
    filter_value = st.text_input(f"请输入要过滤的 {filter_column} 的值")

    # Select number of images per page
    images_per_page = st.selectbox("每页显示的图片数量", options=[3, 6, 9, 12], index=0)

    if filter_value:
        display_images_with_pagination(df, filter_column, filter_value, images_per_page)

if __name__ == "__main__":
    main()
