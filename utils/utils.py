import os

def save_uploaded_file(uploaded_file):
    if uploaded_file is not None:
        save_path = "uploads"  # 设定保存路径
        os.makedirs(save_path, exist_ok=True)  # 创建文件夹（如果不存在）

        # 获取基础文件名和扩展名
        base_name, ext = os.path.splitext(uploaded_file.name)
        file_path = os.path.join(save_path, uploaded_file.name)

        # 检查文件是否存在，若存在则重命名
        counter = 1
        while os.path.exists(file_path):
            file_path = os.path.join(save_path, f"{base_name}_{counter}{ext}")
            counter += 1

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return file_path  # 返回保存的文件路径
    return None