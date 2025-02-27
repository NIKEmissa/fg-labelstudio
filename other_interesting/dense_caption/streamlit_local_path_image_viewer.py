import os
from PIL import Image
import streamlit as st
import pyperclip

# Function to load image from URL with caching
@st.cache_resource
def load_image(image_path):
    try:
        img = Image.open(image_path)
        return img
    except Exception as e:
        st.error(f"加载图片失败: {e}")
        return None

# Function to recursively find all image files in a directory
def get_all_image_files(directory):
    image_files = []
    for root, _, files in os.walk(directory):  # Recursively walk through subdirectories
        if 'mask' in root: continue
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):  # Check if the file is an image
                image_files.append(os.path.join(root, file))
    return image_files

# Function to display images with pagination in n x n grid
def display_images_with_pagination(image_files, images_per_page=3):
    total_images = len(image_files)
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
    page_images = image_files[start_idx:end_idx]
    
    # Calculate number of rows and columns for the grid (n x n grid)
    n = int(images_per_page ** 0.5)  # Square grid (n x n)
    num_rows = (images_per_page + n - 1) // n  # Number of rows needed
    
    # Create a grid for displaying images
    for row_idx in range(num_rows):
        cols = st.columns(n)
        for col_idx in range(n):
            image_idx = row_idx * n + col_idx
            if image_idx < len(page_images):
                image_path = page_images[image_idx]
                with cols[col_idx]:
                    # Display the image
                    st.image(load_image(image_path), caption=f"图片路径: {image_path}", use_container_width=True)
                    # Add a button to copy the URL to clipboard
                    if st.button(f"复制 {image_path} 到剪贴板", key=f"copy_{image_idx}"):
                        pyperclip.copy(image_path)  # Copy URL to clipboard
                        st.success(f"已复制: {image_path}")  # Show success message
    
    # Show current page number
    st.write(f"当前页数: {st.session_state.current_page}/{total_pages}") 

# Streamlit App
def main():
    # Root directory where datasets are stored
    root_dir = "/data1/datasets/lqp/data/denseData/"  # Adjust this path to your root directory

    # Get list of subdirectories (datasets)
    datasets = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
    
    # Let user select dataset
    selected_dataset = st.selectbox("选择数据集", datasets)
    dataset_dir = os.path.join(root_dir, selected_dataset)

    # Get all image files in the selected dataset directory (recursively)
    image_files = get_all_image_files(dataset_dir)

    # Streamlit UI
    st.title("图片查看器")
    
    # Select number of images per page
    images_per_page = st.selectbox("每页显示的图片数量", options=[3, 6, 9, 12], index=0)

    # Display images with pagination
    display_images_with_pagination(image_files, images_per_page)

if __name__ == "__main__":
    main()
