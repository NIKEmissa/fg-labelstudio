import streamlit as st
import os
import pandas as pd
import numpy as np
from urllib.parse import urlparse
import uuid
import time
import shutil
import re

def extract_comment_and_base(s):
    print(s)
    # 找到最后一个 "__" 的位置
    last_underscore_index = s.rfind('__')
    
    if last_underscore_index != -1:
        # 提取 comment
        comment = s[last_underscore_index + 2:]
        # 去掉 comment 部分
        s_without_comment = s[:last_underscore_index]
    else:
        # 没有 "__"，则 comment 为空，s_without_comment 去掉后缀
        comment = ''
        s_without_comment = s

    return comment, s_without_comment


def split_and_extract_comment(s):
    # 提取 comment 和去掉 comment 的字符串
    comment, s_without_comment = extract_comment_and_base(s)

    data_dict = {}
    start = 0  # 初始化 start 变量
    # 找到所有 @ 的索引
    at_indices = [i for i, char in enumerate(s_without_comment) if char == '@']
    
    for index in at_indices:
        # 找到 @ 后第一个 _
        next_index = s_without_comment.find('_', index)
        if next_index != -1:
            field_name = s_without_comment[start:index].strip('_')
            field_value = s_without_comment[index + 1:next_index]
            data_dict[field_name] = field_value
            
            start = next_index + 1  # 更新起始位置为下一个字符

    # 处理最后一个 @ 的特殊情况
    if start < len(s_without_comment):
        print(s_without_comment)
        last_field_name = s_without_comment[start:].strip('_')
        last_field_value = s_without_comment[start:].rsplit('@', 1)[-1] if '@' in s_without_comment[start:] else ''
        
        if '@' in last_field_name:
            last_field_name, last_field_value = last_field_name.split('@', 1)
        
        data_dict[last_field_name] = last_field_value
    
    # 添加 comment 字段
    data_dict['comment'] = comment
    
    return data_dict

# 创建DataFrame，从上传的txt文件解析内容
def parse_uploaded_files(uploaded_files, split_version):

    print(f">>>>>>>>>{split_version}")
    
    if split_version == "0":
        image_paths = []
        img_ids = []
        model_ids = []
        guidances = []
        img_seq_lens = []
        sizes = []
        seeds = []
        customed_tags = []

        for uploaded_file in uploaded_files:
            lines = uploaded_file.readlines()
            for line in lines:
                line = line.decode('utf-8').strip()  # 解码为字符串并去除两端空白
                # 提取 URL 中的文件名部分
                path = urlparse(line).path
                file_name = os.path.basename(path).rpartition('.')[0]
                # 分割文件名并解析各个部分
                parts = file_name.split('_')
                if len(parts) == 6:
                    img_ids.append(int(parts[0]))
                    model_ids.append(int(parts[1]))
                    guidances.append(float(parts[2]))
                    img_seq_lens.append(int(parts[3]))
                    sizes.append(parts[4])
                    seeds.append(int(parts[5]))
                    image_paths.append(line)
                    customed_tags.append(str('None'))
                elif len(parts) == 7:
                    img_ids.append(int(parts[0]))
                    model_ids.append(int(parts[1]))
                    guidances.append(float(parts[2]))
                    img_seq_lens.append(int(parts[3]))
                    sizes.append(parts[4])
                    seeds.append(int(parts[5]))
                    image_paths.append(line)
                    customed_tags.append(str(parts[6]))                

        # 创建DataFrame
        df = pd.DataFrame({
            'image_path': image_paths,
            'img_id': img_ids,
            'model_id': model_ids,
            'guidance': guidances,
            'img_seq_len': img_seq_lens,
            'size': sizes,
            'seed': seeds,
            'customed_tags': customed_tags,
        })

        return df
    
    else:

        # 动态解析存储
        dynamic_lists = {'image_path': []}  # 直接初始化 image_path
        image_paths = []

        for uploaded_file in uploaded_files:
            lines = uploaded_file.readlines()
            for line in lines:
                line = line.decode('utf-8').strip()  # 解码为字符串并去除两端空白
                # 提取 URL 中的文件名部分
                path = urlparse(line).path
                file_name = os.path.basename(path).rpartition('.')[0]

                # 使用 split_and_extract_comment 提取键值对
                parsed_data = split_and_extract_comment(file_name)
                for key, value in parsed_data.items():
                    dynamic_lists.setdefault(key, []).append(value)
                    print(key, value)

                image_paths.append(line)

        # 将 image_paths 添加到 dynamic_lists
        dynamic_lists['image_path'] = image_paths

        # 创建 DataFrame
        df = pd.DataFrame.from_dict(dynamic_lists, orient='index').transpose()

        return df
    
 
def generate_summary_table(filtered_df, row_fields, col_fields):
    row_combinations = []
    col_combinations = []

    # 定义一个函数来检查列是否可以完全转换为数值
    def is_numeric_column(column):
        try:
            pd.to_numeric(column)
            return True
        except ValueError:
            return False

    # 定义一个通用的排序键函数
    def custom_sort_key(series):
        if is_numeric_column(series):
            return pd.to_numeric(series, errors='coerce').fillna(float('inf'))
        else:
            return series

    # 根据用户选择的行字段生成唯一组合并排序
    unique_row_combinations = filtered_df[row_fields].drop_duplicates()
    unique_row_combinations = unique_row_combinations.sort_values(by=row_fields, key=custom_sort_key)

    for _, row in unique_row_combinations.iterrows():
        row_combinations.append(tuple(row[row_fields]))

    # 根据用户选择的列字段生成唯一组合并排序
    unique_col_combinations = filtered_df[col_fields].drop_duplicates()
    unique_col_combinations = unique_col_combinations.sort_values(by=col_fields, key=custom_sort_key)

    for _, row in unique_col_combinations.iterrows():
        col_combinations.append(tuple(row[col_fields]))

    summary_table = np.empty((len(row_combinations), len(col_combinations)), dtype=object)
    summary_table[:] = ''  # 初始化为空字符串

    # 填充表格内容
    for _, row in filtered_df.iterrows():
        row_value = tuple(row[row_fields])
        col_value = tuple(row[col_fields])
        try:
            row_idx = row_combinations.index(row_value)
            col_idx = col_combinations.index(col_value)
            summary_table[row_idx, col_idx] = row['image_path']
        except ValueError:
            continue

    return summary_table, row_combinations, col_combinations

def generate_html_page(summary_table, row_combinations, col_combinations, row_fields, col_fields, img_id, output_path='output_html'):
    # 构建表格结构
    num_rows = len(row_fields)
    num_cols = len(col_fields)
    data_size = len(row_combinations)  # 根据实际行组合数量

    # 初始化表格，使用空字符串填充
    header = [['' for _ in range(num_rows + len(col_combinations))] for _ in range(num_cols + 1 + data_size)]

    # 填充行字段表头
    for i in range(num_rows):
        header[num_cols][i] = row_fields[i]

    # 填充列字段表头
    for j in range(num_cols):
        header[j][num_rows - 1] = col_fields[j]

    # 填充列字段的值
    for i in range(len(col_combinations)):
        for j in range(num_cols):
            header[j][i + num_rows] = col_combinations[i][j]

    # 填充行字段的值
    for i in range(len(row_combinations)):
        for j in range(num_rows):
            header[i + num_cols + 1][j] = row_combinations[i][j]

    # 填充表格数据部分并添加表头信息到图片格
    for i in range(len(row_combinations)):
        for j in range(len(col_combinations)):
            cell_value = summary_table[i, j] if summary_table[i, j] else "图片占位符"
            if isinstance(cell_value, str) and cell_value.startswith('http'):
                # 构建表头名：表头值的字符串
                header_info = []
                for row_field, row_value in zip(row_fields, row_combinations[i]):
                    header_info.append(f"{row_field}: {row_value}")
                for col_field, col_value in zip(col_fields, col_combinations[j]):
                    header_info.append(f"{col_field}: {col_value}")
                header_text = ", ".join(header_info)
                # 在图片上添加表头信息
                header[i + num_cols + 1][j + num_rows] = f"<div>{header_text}</div><img src='{cell_value}' alt='Image' class='zoomable'>"
            else:
                header[i + num_cols + 1][j + num_rows] = cell_value

    # 生成HTML表格
    html_content = f"""
    <html>
    <head>
        <title>Debug Table Visualization - img_id: {img_id}</title>
        <style>
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            table, th, td {{
                border: 1px solid black;
            }}
            th, td {{
                padding: 10px;
                text-align: center;
            }}
            img {{
                max-width: 200px;
                max-height: 200px;
                cursor: zoom-in;
                transition: transform 0.3s ease;
            }}
            img.fullscreen {{
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) scale(2);
                cursor: zoom-out;
                z-index: 1000;
            }}
            .overlay {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: rgba(0, 0, 0, 0.7);
                z-index: 999;
            }}
        </style>
    </head>
    <body>
        <h1>Debug Table Visualization - img_id: {img_id}</h1>
        <table>
    """

    # 添加表头行
    for row in header[:num_cols + 1]:
        html_content += "<tr>"
        for cell in row:
            html_content += f"<th>{cell}</th>" if cell != '' else "<th></th>"
        html_content += "</tr>"

    # 添加数据部分
    for row in header[num_cols + 1:]:
        html_content += "<tr>"
        for cell in row:
            if isinstance(cell, str) and cell.startswith('<div>'):
                html_content += f"<td>{cell}</td>"
            elif isinstance(cell, str) and cell.startswith('http'):
                html_content += f"<td><img src='{cell}' alt='Image' class='zoomable'></td>"
            else:
                html_content += f"<td>{cell}</td>" if cell != '' else "<td></td>"
        html_content += "</tr>"

    html_content += """
        </table>
        <script>
            document.addEventListener("DOMContentLoaded", function () {{
                const images = document.querySelectorAll("img.zoomable");

                images.forEach(image => {{
                    let scaleLevel = 1;
                    let isDragging = false;
                    let startX, startY;
                    let offsetX = 0, offsetY = 0;

                    image.addEventListener("mousedown", function (event) {{
                        if (this.classList.contains("fullscreen")) {{
                            isDragging = true;
                            startX = event.clientX - offsetX;
                            startY = event.clientY - offsetY;
                        }}
                    }});

                    document.addEventListener("mousemove", function (event) {{
                        if (isDragging) {{
                            offsetX = event.clientX - startX;
                            offsetY = event.clientY - startY;
                            image.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scaleLevel})`;
                        }}
                    }});

                    document.addEventListener("mouseup", function () {{
                        isDragging = false;
                    }});

                    image.addEventListener("click", function (event) {{
                        if (event.ctrlKey) {{
                            if (scaleLevel > 1) {{
                                scaleLevel -= 1;
                                this.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scaleLevel})`;
                            }} else {{
                                document.querySelector(".overlay")?.remove();
                                this.classList.remove("fullscreen");
                                scaleLevel = 1;
                                offsetX = 0;
                                offsetY = 0;
                                this.style.transform = `translate(-50%, -50%) scale(${scaleLevel})`;
                            }}
                        }} else {{
                            if (!this.classList.contains("fullscreen")) {{
                                const overlay = document.createElement("div");
                                overlay.classList.add("overlay");
                                document.body.appendChild(overlay);

                                this.classList.add("fullscreen");
                                scaleLevel = 2;
                                offsetX = 0;
                                offsetY = 0;
                            }} else if (scaleLevel < 1000) {{
                                scaleLevel += 1;
                                this.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scaleLevel})`;
                            }}
                        }}
                    }});
                }});

                document.body.addEventListener("click", function (event) {{
                    if (event.target.classList.contains("overlay")) {{
                        document.querySelector(".overlay")?.remove();
                        const fullscreenImage = document.querySelector("img.fullscreen");
                        if (fullscreenImage) {{
                            fullscreenImage.classList.remove("fullscreen");
                            fullscreenImage.style.transform = "scale(1)";
                        }}
                    }}
                }});
            }});
        </script>
    </body>
    </html>
    """

    # 保存HTML文件
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    output_file = os.path.join(output_path, f'debug_table_{img_id}.html')
    with open(output_file, 'w') as file:
        file.write(html_content)

        
@st.fragment()
def download_without_reload(file_path, filename):
    with open(file_path, "rb") as file:
        st.download_button(
            label=f"下载 {filename}",
            data=file,
            file_name=filename,
            mime="text/html"
        )

@st.fragment()
def download_zip_file(zip_path, filename):
    with open(zip_path, "rb") as zip_file:
        st.download_button(
            label=f"下载整个压缩文件（点了按钮会反应段时间，请耐心）: {filename}",
            data=zip_file,
            file_name=filename,
            mime="application/zip"
        )

# Streamlit应用主函数
def flux_to_html():
    st.title("HTML Generator from Uploaded Text Files")

    # 上传文件
    uploaded_files = st.file_uploader("上传所有的txt文件", type=["txt"], accept_multiple_files=True)
    # 定义前端显示的选项和后端实际使用的值的映射字典
    option_mapping = {
        "老格式选这个": "0",
        "新格式选这个（带@的）": "1",
    }

    # 创建单选按钮，用户的选择将存储在变量selected_option_display中
    selected_option_display = st.radio("Choose an option", list(option_mapping.keys()))

    # 获取后端实际使用的值
    selected_option_value = option_mapping[selected_option_display]
    
    if uploaded_files:
        # 解析上传的文件
        df = parse_uploaded_files(uploaded_files, selected_option_value)

        # 根据DataFrame的列动态生成可选字段
        available_fields = df.columns.tolist()
        # 剔除不需要的字段
        excluded_fields = ['image_path', 'comment']
        select_fields = [field for field in available_fields if field not in excluded_fields]
        
        # 允许用户选择行和列的字段
        st.subheader("选择划分表格的字段")        
        html_spliter = st.selectbox("选择用于划分表的字段（表）", select_fields + ["None:选这个，则在同一个HTML放入所有字段"])  # 默认选择前两个字段
        select_fields = [field for field in select_fields if field not in html_spliter]

        row_fields = st.multiselect("选择用于生成表格的字段（行）", select_fields, default=select_fields[1:])  # 默认选择前两个字段
        select_col_fields = [field for field in select_fields if field not in row_fields]
        col_fields = st.multiselect("选择用于生成表格的字段（列）", select_col_fields, default=[select_col_fields[0]])  # 默认选择第一个字段     

        # 用户选择具体的维度值
        st.subheader("选择维度值")
        dimension_values = {}
        for field in select_fields:
            if field in df.columns:
                dimension_values[field] = st.multiselect(f"选择{field}值", sorted(df[field].unique()), default=sorted(df[field].unique()))

        # 增加Run按钮
        if st.button("Run"):
            unique_id = str(uuid.uuid4())  
            timestamp = int(time.time())
            output_path = f'output_html/output_html_{unique_id}_{timestamp}'
            zip_path = f'{output_path}.zip'

            if not os.path.exists(output_path):
                os.makedirs(output_path)

            # 生成HTML文件
            with st.spinner("正在生成HTML文件，请稍候..."):
                unique_img_ids = df[html_spliter].unique() if ("None" not in html_spliter) else ["None"]
                for img_id in unique_img_ids:
                    filtered_df = df[df[html_spliter] == img_id] if ("None" not in html_spliter) else df
                    for field in dimension_values:
                        filtered_df = filtered_df[filtered_df[field].isin(dimension_values[field])]
                    
                    summary_table, row_combinations, col_combinations = generate_summary_table(
                        filtered_df,
                        row_fields,
                        col_fields
                    )
                    generate_html_page(summary_table, row_combinations, col_combinations, row_fields, col_fields, img_id, output_path)

            # 压缩输出文件夹为ZIP
            shutil.make_archive(output_path, 'zip', output_path)

            st.success("HTML文件生成成功！")
            download_zip_file(zip_path, f'output_html_{unique_id}_{timestamp}.zip')

            # 下载单个HTML文件
            for filename in os.listdir(output_path):
                file_path = os.path.join(output_path, filename)
                download_without_reload(file_path, filename)