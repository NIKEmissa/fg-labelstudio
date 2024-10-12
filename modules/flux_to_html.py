import streamlit as st
import os
import pandas as pd
import numpy as np
from urllib.parse import urlparse
import uuid
import time

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
def generate_summary_table(filtered_df, selected_guidances, selected_model_ids, selected_img_seq_lens, selected_sizes, selected_seeds):
    model_img_seq_size_seed_pairs = []

    # 根据用户选择的维度值进行过滤和排序组合
    model_id_values = [val for val in sorted(filtered_df['model_id'].unique()) if val in selected_model_ids]
    img_seq_len_values = [val for val in sorted(filtered_df['img_seq_len'].unique()) if val in selected_img_seq_lens]
    size_values = [val for val in sorted(filtered_df['size'].unique()) if val in selected_sizes]
    seed_values = [val for val in sorted(filtered_df['seed'].unique()) if val in selected_seeds]

    # 生成 model_id, img_seq_len, size, seed 的组合
    for model_id in model_id_values:
        for img_seq_len in img_seq_len_values:
            for size in size_values:
                for seed in seed_values:
                    if len(filtered_df[
                        (filtered_df['model_id'] == model_id) &
                        (filtered_df['img_seq_len'] == img_seq_len) &
                        (filtered_df['size'] == size) &
                        (filtered_df['seed'] == seed)
                    ]) > 0:
                        model_img_seq_size_seed_pairs.append((model_id, img_seq_len, size, seed))

    guide_values = [val for val in sorted(filtered_df['guidance'].unique()) if val in selected_guidances]

    summary_table = np.empty((len(model_img_seq_size_seed_pairs), len(guide_values)), dtype=object)
    summary_table[:] = ''  # 初始化为空字符串

    # 填充表格内容
    for _, row in filtered_df.iterrows():
        model_id, img_seq_len, size, seed, guidance = row['model_id'], row['img_seq_len'], row['size'], row['seed'], row['guidance']
        if model_id in selected_model_ids and img_seq_len in selected_img_seq_lens and size in selected_sizes and seed in selected_seeds and guidance in selected_guidances:
            model_img_seq_size_seed_idx = model_img_seq_size_seed_pairs.index((model_id, img_seq_len, size, seed))
            guide_idx = guide_values.index(guidance)
            summary_table[model_img_seq_size_seed_idx, guide_idx] = row['image_path']

    return summary_table, model_img_seq_size_seed_pairs, guide_values

# 生成HTML页面以查看图像
def generate_html_page(summary_table, model_img_seq_size_seed_pairs, guide_values, img_id, output_path='output_html'):
    html_content = """
    <html>
    <head>
        <title>Summary Table Visualization</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            table, th, td {
                border: 1px solid black;
            }
            th, td {
                padding: 10px;
                text-align: center;
            }
            img {
                max-width: 200px;
                max-height: 200px;
                cursor: zoom-in;
                transition: transform 0.3s ease;
            }
            img.fullscreen {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) scale(2);
                cursor: zoom-out;
                z-index: 1000;
            }
            .overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: rgba(0, 0, 0, 0.7);
                z-index: 999;
            }
        </style>
    </head>
    <body>
        <h1>Summary Table Visualization - img_id: """ + str(img_id) + """</h1>
        <table>
            <tr>
    """

    # 添加表格标题
    html_content += "<th>model_id</th><th>img_seq_len</th><th>size</th><th>seed</th>"
    for guide in guide_values:
        html_content += f"<th>{guide}</th>"
    html_content += "</tr>"
    
    model_id_set = set([])
    for i, (model_id, img_seq_len, size, seed) in enumerate(model_img_seq_size_seed_pairs):
        model_id_set.add(str(model_id))
        html_content += "<tr>"
        html_content += f"<td>{model_id}</td><td>{img_seq_len}</td><td>{size}</td><td>{seed}</td>"

        for j in range(len(guide_values)):
            image_path = summary_table[i, j]
            if image_path:
                html_content += f"<td><img src='{image_path}' alt='Image' class='zoomable'></td>"
            else:
                html_content += "<td></td>"
        html_content += "</tr>"

    html_content += """
        </table>
        <script>
            document.addEventListener("DOMContentLoaded", function () {
                const images = document.querySelectorAll("img.zoomable");

                images.forEach(image => {
                    let scaleLevel = 1;
                    let isDragging = false;
                    let startX, startY;
                    let offsetX = 0, offsetY = 0;

                    image.addEventListener("mousedown", function (event) {
                        if (this.classList.contains("fullscreen")) {
                            isDragging = true;
                            startX = event.clientX - offsetX;
                            startY = event.clientY - offsetY;
                        }
                    });

                    document.addEventListener("mousemove", function (event) {
                        if (isDragging) {
                            offsetX = event.clientX - startX;
                            offsetY = event.clientY - startY;
                            image.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scaleLevel})`;
                        }
                    });

                    document.addEventListener("mouseup", function () {
                        isDragging = false;
                    });

                    image.addEventListener("click", function (event) {
                        if (event.ctrlKey) {
                            if (scaleLevel > 1) {
                                scaleLevel -= 1;
                                this.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scaleLevel})`;
                            } else {
                                document.querySelector(".overlay")?.remove();
                                this.classList.remove("fullscreen");
                                scaleLevel = 1;
                                offsetX = 0;
                                offsetY = 0;
                                this.style.transform = `translate(-50%, -50%) scale(${scaleLevel})`;
                            }
                        } else {
                            if (!this.classList.contains("fullscreen")) {
                                const overlay = document.createElement("div");
                                overlay.classList.add("overlay");
                                document.body.appendChild(overlay);

                                this.classList.add("fullscreen");
                                scaleLevel = 2;
                                offsetX = 0;
                                offsetY = 0;
                            } else if (scaleLevel < 1000) {
                                scaleLevel += 1;
                                this.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scaleLevel})`;
                            }
                        }
                    });
                });

                document.body.addEventListener("click", function (event) {
                    if (event.target.classList.contains("overlay")) {
                        document.querySelector(".overlay")?.remove();
                        const fullscreenImage = document.querySelector("img.fullscreen");
                        if (fullscreenImage) {
                            fullscreenImage.classList.remove("fullscreen");
                            fullscreenImage.style.transform = "scale(1)";
                        }
                    }
                });
            });
        </script>
    </body>
    </html>
    """
    
    formatted_model_id = ['modelID{0}'.format(i) for i in model_id_set]
    model_id_str = "_".join(formatted_model_id)
    output_file = os.path.join(output_path, f'{img_id}_{model_id_str}.html')
    with open(output_file, 'w') as file:
        file.write(html_content)

def flux_to_html():
    st.title("HTML Generator from Uploaded Text Files")

    # 上传文件
    uploaded_files = st.file_uploader("上传所有的txt文件", type=["txt"], accept_multiple_files=True)

    if uploaded_files:
        # 解析上传的文件
        df = parse_uploaded_files(uploaded_files)

        # 用户选择具体的维度值
        st.subheader("选择维度值")
        selected_guidances = st.multiselect("选择guidance值", sorted(df['guidance'].unique()), default=sorted(df['guidance'].unique()))
        selected_model_ids = st.multiselect("选择model_id值", sorted(df['model_id'].unique()), default=sorted(df['model_id'].unique()))
        selected_img_seq_lens = st.multiselect("选择img_seq_len值", sorted(df['img_seq_len'].unique()), default=sorted(df['img_seq_len'].unique()))
        selected_sizes = st.multiselect("选择size值", sorted(df['size'].unique()), default=sorted(df['size'].unique()))
        selected_seeds = st.multiselect("选择seed值", sorted(df['seed'].unique()), default=sorted(df['seed'].unique()))

        # 增加Run按钮
        if st.button("Run"):
            # 创建唯一的 output_path
            unique_id = str(uuid.uuid4())  # 生成唯一的 UUID
            timestamp = int(time.time())  # 获取当前时间戳
            output_path = f'output_html/output_html_{unique_id}_{timestamp}'
            
            # 创建 output_path 文件夹
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            # 生成HTML文件
            with st.spinner("正在生成HTML文件，请稍候..."):
                unique_img_ids = df['img_id'].unique()
                for img_id in unique_img_ids:
                    filtered_df = df[df['img_id'] == img_id]
                    summary_table, model_img_seq_size_seed_pairs, guide_values = generate_summary_table(
                        filtered_df,
                        selected_guidances,
                        selected_model_ids,
                        selected_img_seq_lens,
                        selected_sizes,
                        selected_seeds
                    )
                    generate_html_page(summary_table, model_img_seq_size_seed_pairs, guide_values, img_id, output_path)

            # 提供下载链接
            st.success("HTML文件生成成功！")
            for filename in os.listdir(output_path):
                file_path = os.path.join(output_path, filename)
                with open(file_path, "rb") as file:
                    st.download_button(
                        label=f"下载 {filename}",
                        data=file,
                        file_name=filename,
                        mime="text/html"
                    )
