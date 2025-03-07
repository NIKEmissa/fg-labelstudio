import streamlit as st
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import requests
from io import BytesIO
import pandas as pd

# 解析日志的函数
def parse_log(log_data):
    log = log_data
    log_info = {
        "id": log.get("id"),
        "isInvalid": log.get("isInvalid"),
    }
    
    picture_info = []
    if "pictureList" in log:
        for picture in log["pictureList"]:
            picture_details = {
                "id": picture.get("id"),
                "url": picture.get("url"),
                "isInvalid": picture.get("isInvalid"),
            }
            picture_info.append(picture_details)
    
    labels_info = []
    if "labels" in log:
        labels = json.loads(log["labels"])
        for label in labels:
            label_info = {
                "tag": label.get("tag", {}).get("name"),
                "additionalAnnotation": label.get("additionalAnnotation"),
                "dimensionValues": [],
                "boxes": []  # 保存框的坐标
            }
            if "points" in label:
                # 提取标注框的坐标 (points)
                if len(label["points"]) == 2:
                    point1, point2 = label["points"]
                    x1, y1 = point1["x"], point1["y"]
                    x2, y2 = point2["x"], point2["y"]
                    # 计算矩形框的宽度和高度
                    width = abs(x2 - x1)
                    height = abs(y2 - y1)
                    label_info["boxes"].append((x1, y1, width, height))

            if "dimensionList" in label:
                for dimension in label["dimensionList"]:
                    dimension_info = {
                        "name": dimension.get("name"),
                        "dimensionValues": []
                    }
                    if "dimensionValueList" in dimension:
                        for value in dimension["dimensionValueList"]:
                            dimension_info["dimensionValues"].append(value.get("name"))
                    label_info["dimensionValues"].append(dimension_info)
            labels_info.append(label_info)
    
    return {
        "log_info": log_info,
        "picture_info": picture_info,
        "labels_info": labels_info,
    }

# 对比两个标注员的标注结果并可视化
def compare_annotations(log1, log2):
    parsed_data1 = parse_log(log1)
    parsed_data2 = parse_log(log2)
    
    # 获取图片的URL
    img_url = parsed_data1['picture_info'][0]['url']
    
    # 下载图片
    response = requests.get(img_url)
    img = Image.open(BytesIO(response.content))

    # 创建Matplotlib图像
    fig, ax = plt.subplots(figsize=(10, 10))

    # 绘制图片
    ax.imshow(img)
    ax.set_title("标注员1与标注员2的标注对比")

    # 绘制标注框（标注员1 - 蓝色）
    for label in parsed_data1['labels_info']:
        for box in label['boxes']:
            if box:  # 确保框存在
                x1, y1, width, height = box
                rect = patches.Rectangle((x1, y1), width, height, linewidth=2, edgecolor='blue', facecolor='none', label="标注员1")
                ax.add_patch(rect)

    # 绘制标注框（标注员2 - 红色）
    for label in parsed_data2['labels_info']:
        for box in label['boxes']:
            if box:  # 确保框存在
                x1, y1, width, height = box
                rect = patches.Rectangle((x1, y1), width, height, linewidth=2, edgecolor='red', facecolor='none', label="标注员2")
                ax.add_patch(rect)

    # 在col1中显示图片
    col1, col2 = st.columns([1, 1])

    with col1:
        st.pyplot(fig)

    # 对比标注结果，显示在col2
    with col2:
        table_data = []
        
        for i, label1 in enumerate(parsed_data1["labels_info"]):
            label2 = parsed_data2["labels_info"][i]  # 假设两个标注员的顺序一致
            for dim1, dim2 in zip(label1["dimensionValues"], label2["dimensionValues"]):
                row = {"维度": dim1["name"]}
                for value1, value2 in zip(dim1["dimensionValues"], dim2["dimensionValues"]):
                    # 如果不相同，高亮显示
                    if value1 != value2:
                        row["标注员1"] = f"<span style='color:red'>{value1}</span>"
                        row["标注员2"] = f"<span style='color:red'>{value2}</span>"
                    else:
                        row["标注员1"] = value1
                        row["标注员2"] = value2
                table_data.append(row)

        # 创建并展示表格
        df = pd.DataFrame(table_data)
        st.markdown(df.to_html(escape=False), unsafe_allow_html=True)

# 主界面逻辑
def main():
    # 设置宽屏模式
    st.set_page_config(layout="wide")
        
    st.title("标注结果对比")
    
    st.write("请选择要对比的标注结果：")

    # 上传文件
    uploaded_file1 = st.file_uploader("上传第一个标注员的标注结果文件", type="txt")
    uploaded_file2 = st.file_uploader("上传第二个标注员的标注结果文件", type="txt")

    if uploaded_file1 is not None and uploaded_file2 is not None:
        # 读取并解析文件
        rst1 = json.load(uploaded_file1)
        rst2 = json.load(uploaded_file2)

        # 增加一个选项来决定是否进行过滤
        filter_option = st.selectbox("是否只选择两个标注员都有标注结果的log_id？", ["全部", "仅有两个标注员标注的结果"])

        # 获取所有的log_id
        all_log_ids = [log["id"] for log in rst1]

        if filter_option == "仅有两个标注员标注的结果":
            # 过滤出两个标注员都有标注的log_id
            filtered_log_ids = [log_id for log_id in all_log_ids if any(log1["id"] == log_id for log1 in rst1) and any(log2["id"] == log_id for log2 in rst2)]
            all_log_ids = filtered_log_ids

        # 按照log_id数字大小排序
        all_log_ids.sort(key=lambda x: int(x))  # 将log_id作为整数排序

        # 选择要对比的标注数据
        log_id = st.selectbox("选择要对比的标注结果", all_log_ids)

        # 获取对应的标注数据
        log1 = next(log for log in rst1 if log["id"] == log_id)
        log2 = next(log for log in rst2 if log["id"] == log_id)

        # 显示对比结果
        compare_annotations(log1, log2)
    else:
        st.write("请上传两个标注员的标注结果文件（txt格式）。")

if __name__ == "__main__":
    main()
