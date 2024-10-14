import streamlit as st
import os
import pandas as pd
import numpy as np
from urllib.parse import urlparse
import uuid
import time
import shutil

# 创建DataFrame，从上传的txt文件解析内容
def parse_uploaded_files(uploaded_files):
    image_paths = []
    img_ids = []
    model_ids = []
    guidances = []
    img_seq_lens = []
    sizes = []
    seeds = []

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

    # 创建DataFrame
    df = pd.DataFrame({
        'image_path': image_paths,
        'img_id': img_ids,
        'model_id': model_ids,
        'guidance': guidances,
        'img_seq_len': img_seq_lens,
        'size': sizes,
        'seed': seeds
    })

    return df

# 生成整理表格
def generate_summary_table(filtered_df, row_fields, col_fields):
    row_combinations = []
    col_combinations = []

    # 根据用户选择的行字段生成唯一组合并排序
    unique_row_combinations = filtered_df[row_fields].drop_duplicates().sort_values(by=row_fields)
    for _, row in unique_row_combinations.iterrows():
        row_combinations.append(tuple(row[row_fields]))

    # 根据用户选择的列字段生成唯一组合并排序
    unique_col_combinations = filtered_df[col_fields].drop_duplicates().sort_values(by=col_fields)
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

    # 填充表格数据部分
    for i in range(len(row_combinations)):
        for j in range(len(col_combinations)):
            header[i + num_cols + 1][j + num_rows] = summary_table[i, j] if summary_table[i, j] else "图片占位符"

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
            if isinstance(cell, str) and cell.startswith('http'):
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

    if uploaded_files:
        # 解析上传的文件
        df = parse_uploaded_files(uploaded_files)

        # 允许用户选择行和列的字段
        available_fields = ['img_id', 'model_id', 'guidance', 'img_seq_len', 'size', 'seed']
        row_fields = st.multiselect("选择用于生成表格的字段（行）", available_fields, default=['model_id', 'img_seq_len', 'size', 'seed'])
        col_fields = st.multiselect("选择用于生成表格的字段（列）", available_fields, default=['guidance'])

        # 用户选择具体的维度值
        st.subheader("选择维度值")
        selected_model_ids = st.multiselect("选择model_id值", sorted(df['model_id'].unique()), default=sorted(df['model_id'].unique()))
        selected_img_seq_lens = st.multiselect("选择img_seq_len值", sorted(df['img_seq_len'].unique()), default=sorted(df['img_seq_len'].unique()))
        selected_sizes = st.multiselect("选择size值", sorted(df['size'].unique()), default=sorted(df['size'].unique()))
        selected_seeds = st.multiselect("选择seed值", sorted(df['seed'].unique()), default=sorted(df['seed'].unique()))
        selected_guidances = st.multiselect("选择guidance值", sorted(df['guidance'].unique()), default=sorted(df['guidance'].unique()))

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
                unique_img_ids = df['img_id'].unique()
                for img_id in unique_img_ids:
                    filtered_df = df[df['img_id'] == img_id]
                    filtered_df = filtered_df[
                        (filtered_df['model_id'].isin(selected_model_ids)) &
                        (filtered_df['img_seq_len'].isin(selected_img_seq_lens)) &
                        (filtered_df['size'].isin(selected_sizes)) &
                        (filtered_df['seed'].isin(selected_seeds)) &
                        (filtered_df['guidance'].isin(selected_guidances))
                    ]
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