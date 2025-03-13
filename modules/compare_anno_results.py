import streamlit as st
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import requests
from io import BytesIO
import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment

import matplotlib
import matplotlib.font_manager as fm

# ----------------------------
# 中文字体设置（确保系统中存在该字体）
# ----------------------------
font_path = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
fm.fontManager.addfont(font_path)
font_name = fm.FontProperties(fname=font_path).get_name()
print("实际字体名称：", font_name)  # 例如输出 "Noto Sans CJK JP"
matplotlib.rcParams['font.family'] = font_name
matplotlib.rcParams['font.sans-serif'] = [font_name]
matplotlib.rcParams['axes.unicode_minus'] = False

# ----------------------------
# 工具函数
# ----------------------------
def compute_iou(box1, box2):
    # box 格式：(x, y, width, height)
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    xA = max(x1, x2)
    yA = max(y1, y2)
    xB = min(x1 + w1, x2 + w2)
    yB = min(y1 + h1, y2 + h2)
    inter_area = max(0, xB - xA) * max(0, yB - yA)
    box1_area = w1 * h1
    box2_area = w2 * h2
    union_area = box1_area + box2_area - inter_area
    if union_area == 0:
        return 0
    return inter_area / union_area

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
                # 当 points 数量为2时，解析为矩形框
                if len(label["points"]) == 2:
                    point1, point2 = label["points"]
                    x1, y1 = point1["x"], point1["y"]
                    x2, y2 = point2["x"], point2["y"]
                    # 保证 x,y 为左上角坐标
                    x, y = min(x1, x2), min(y1, y2)
                    width = abs(x2 - x1)
                    height = abs(y2 - y1)
                    label_info["boxes"].append((x, y, width, height))
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

def match_boxes(boxes1, boxes2, threshold=0.3, debug=False):
    # boxes1、boxes2 为列表，每一项为 (box, annotation)
    n1 = len(boxes1)
    n2 = len(boxes2)
    print(n1, n2)
    cost_matrix = np.zeros((n1, n2))
    iou_matrix = np.zeros((n1, n2))
    for i, (box1, _) in enumerate(boxes1):
        for j, (box2, _) in enumerate(boxes2):
            iou = compute_iou(box1, box2)
            cost_matrix[i, j] = 1 - iou  # cost 越小匹配越好
            iou_matrix[i, j] = iou
    if debug:
        st.header("debug: 匹配框iou_matrix")
        st.table(iou_matrix)
    
    matched_pairs = []
    # 采用类似 NMS 的思想，不过滤框，仅分组：当 IoU >= threshold 时，归为一组
    for i, (box1, ann1) in enumerate(boxes1):
        for j, (box2, ann2) in enumerate(boxes2):
            iou = compute_iou(box1, box2)
            if iou >= threshold:
                matched_pairs.append(((box1, ann1), (box2, ann2), iou))
                if debug:
                    st.write(f"debug: 匹配到框：Annotator1 box {box1} 与 Annotator2 box {box2}，IoU = {iou:.2f}")
    return matched_pairs

def compute_matched_pairs(log1, log2, debug=False):
    import re
    def clean_tag(tag):
        # 移除尾部数字后缀，如果 tag 为 None 则返回 "UNKNOWN"
        return re.sub(r'\d+$', '', tag) if tag else "UNKNOWN"
    
    parsed_data1 = parse_log(log1)
    parsed_data2 = parse_log(log2)
    
    # ----------------------------
    # 阶段1：提取所有框（不按 tag 分组）
    # ----------------------------
    boxes1 = []
    for ann in parsed_data1['labels_info']:
        tag = ann.get("tag", "UNKNOWN")
        for box in ann["boxes"]:
            boxes1.append((box, ann, tag))
    
    boxes2 = []
    for ann in parsed_data2['labels_info']:
        tag = ann.get("tag", "UNKNOWN")
        for box in ann["boxes"]:
            boxes2.append((box, ann, tag))
    
    # Debug：显示两个标注员提取到的框（文字表格）
    if debug:
        debug_boxes1 = [{"Annotator": "Annotator1", "Tag": item[2], "Box": item[0]} for item in boxes1]
        debug_boxes2 = [{"Annotator": "Annotator2", "Tag": item[2], "Box": item[0]} for item in boxes2]
        st.write("### Debug: 从 Annotator1 中提取到的所有框")
        st.dataframe(pd.DataFrame(debug_boxes1))
        st.write("### Debug: 从 Annotator2 中提取到的所有框")
        st.dataframe(pd.DataFrame(debug_boxes2))
    
    # （可选）如果有图片，则可视化展示提取到的框
    if debug and parsed_data1['picture_info']:
        img_url = parsed_data1['picture_info'][0]['url']
        try:
            response = requests.get(img_url)
            img = Image.open(BytesIO(response.content))
            fig, ax = plt.subplots(figsize=(10, 10))
            ax.imshow(img)
            # 绘制 Annotator1 的框（蓝色）
            for box, ann, tag in boxes1:
                x, y, w, h = box
                rect = patches.Rectangle((x, y), w, h, edgecolor='blue', facecolor='none', linewidth=2)
                ax.add_patch(rect)
                ax.text(x, y, f"{tag} (A1)", color='blue', fontsize=10, backgroundcolor='white')
            # 绘制 Annotator2 的框（红色）
            for box, ann, tag in boxes2:
                x, y, w, h = box
                rect = patches.Rectangle((x, y), w, h, edgecolor='red', facecolor='none', linewidth=2)
                ax.add_patch(rect)
                ax.text(x, y, f"{tag} (A2)", color='red', fontsize=10, backgroundcolor='white')
            st.write("### Debug: 可视化展示提取到的所有框")
            st.pyplot(fig)
        except Exception as e:
            if debug:
                st.write("可视化提取框失败：", e)
    
    # ----------------------------
    # 阶段2：对所有提取到的框进行匹配（仅根据 IoU，不考虑 tag）
    # ----------------------------
    # 为匹配函数准备数据：每项只保留 (box, ann)
    boxes1_for_match = [(box, ann) for box, ann, tag in boxes1]
    boxes2_for_match = [(box, ann) for box, ann, tag in boxes2]
    
    matched_pairs = match_boxes(boxes1_for_match, boxes2_for_match, debug=debug)
    
    # Debug：展示原始匹配结果（表格）
    if debug:
        debug_matches = []
        for idx, (item1, item2, iou) in enumerate(matched_pairs):
            box1, ann1 = item1
            box2, ann2 = item2
            tag1 = ann1.get("tag", "UNKNOWN")
            tag2 = ann2.get("tag", "UNKNOWN")
            debug_matches.append({
                "Pair Index": idx + 1,
                "Annotator1 Tag": tag1,
                "Annotator1 Box": box1,
                "Annotator2 Tag": tag2,
                "Annotator2 Box": box2,
                "IoU": iou
            })
        st.write("### Debug: 原始框匹配结果（不考虑 tag）")
        st.dataframe(pd.DataFrame(debug_matches))
    
    # （可选）可视化原始匹配结果：在图片上画出匹配对，并用虚线连接两个框中心
    if debug and parsed_data1['picture_info']:
        img_url = parsed_data1['picture_info'][0]['url']
        try:
            response = requests.get(img_url)
            img = Image.open(BytesIO(response.content))
            fig, ax = plt.subplots(figsize=(10, 10))
            ax.imshow(img)
            for item1, item2, iou in matched_pairs:
                box1, ann1 = item1
                box2, ann2 = item2
                x1, y1, w1, h1 = box1
                x2, y2, w2, h2 = box2
                rect1 = patches.Rectangle((x1, y1), w1, h1, edgecolor='blue', facecolor='none', linewidth=2)
                rect2 = patches.Rectangle((x2, y2), w2, h2, edgecolor='red', facecolor='none', linewidth=2)
                ax.add_patch(rect1)
                ax.add_patch(rect2)
                center1 = (x1 + w1/2, y1 + h1/2)
                center2 = (x2 + w2/2, y2 + h2/2)
                ax.plot([center1[0], center2[0]], [center1[1], center2[1]], linestyle='--', color='green')
            st.write("### Debug: 可视化原始框匹配结果")
            st.pyplot(fig)
        except Exception as e:
            if debug:
                st.write("可视化原始匹配结果失败：", e)
    
    # ----------------------------
    # 阶段3：对匹配对按 tag 进行过滤和分组（仅保留 tag 相同的匹配对，忽略 tag 尾部数字）
    # ----------------------------
    matched_pairs_list = []
    global_group = 0
    used_boxes1 = set()  # 记录通过匹配使用的 Annotator1 的框（以 tuple 形式记录）
    used_boxes2 = set()  # 记录通过匹配使用的 Annotator2 的框
    for idx, (item1, item2, iou) in enumerate(matched_pairs):
        box1, ann1 = item1
        box2, ann2 = item2
        tag1 = ann1.get("tag", "UNKNOWN")
        tag2 = ann2.get("tag", "UNKNOWN")
        if clean_tag(tag1) == clean_tag(tag2):
            global_group += 1
            matched_pairs_list.append({
                "global_group": global_group,
                "tag": tag1,  # 保留原始 tag
                "pair_index": idx + 1,  # 整体匹配序号
                "box1": box1,
                "ann1": ann1,
                "box2": box2,
                "ann2": ann2,
                "iou": iou
            })
            used_boxes1.add(box1)
            used_boxes2.add(box2)
        else:
            if debug:
                st.write(f"### Debug: 丢弃匹配对 - Annotator1 tag: {tag1} 与 Annotator2 tag: {tag2} 不一致（忽略数字后缀后分别为 {clean_tag(tag1)} 与 {clean_tag(tag2)}）")
    
    if debug:
        st.write("### Debug: 按 tag 过滤后的最终匹配结果")
        st.dataframe(pd.DataFrame(matched_pairs_list))
    
    # ----------------------------
    # 阶段4：记录未匹配上的框
    # ----------------------------
    if debug:
        unmatched_boxes1 = [{"Annotator": "Annotator1", "Tag": tag, "Box": box} for (box, ann, tag) in boxes1 if box not in used_boxes1]
        unmatched_boxes2 = [{"Annotator": "Annotator2", "Tag": tag, "Box": box} for (box, ann, tag) in boxes2 if box not in used_boxes2]
        st.write("### Debug: 未匹配上的框 - Annotator1")
        st.dataframe(pd.DataFrame(unmatched_boxes1))
        st.write("### Debug: 未匹配上的框 - Annotator2")
        st.dataframe(pd.DataFrame(unmatched_boxes2))
    
    return matched_pairs_list

# ----------------------------
# 正常模式下的对比与可视化（支持匹配组选择）
# ----------------------------
def compare_annotations(log1, log2, selected_group, matched_pairs_list):
    # 加载图片（取第一个图片）
    parsed_data1 = parse_log(log1)
    if len(parsed_data1['picture_info']) == 0:
        st.error("无图片信息")
        return
    img_url = parsed_data1['picture_info'][0]['url']
    try:
        response = requests.get(img_url)
        img = Image.open(BytesIO(response.content))
    except Exception as e:
        st.error(f"图片下载失败: {e}")
        return

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(img)
    ax.set_title("标注员1与标注员2的标注对比")
    
    table_data = []
    
    # 根据选择过滤匹配对
    if selected_group == "全部":
        filtered_pairs = matched_pairs_list
    else:
        try:
            group_id = int(selected_group)
        except:
            st.error("选择的匹配组无效")
            return
        filtered_pairs = [pair for pair in matched_pairs_list if pair["global_group"] == group_id]
    
    # 当选择“全部”时，可以（可选）先绘制所有原始框作为参考
    if selected_group == "全部":
        for ann in parsed_data1['labels_info']:
            for box in ann['boxes']:
                x, y, w, h = box
                rect = patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='lightblue', facecolor='none', linestyle="--")
                ax.add_patch(rect)
        parsed_data2 = parse_log(log2)
        for ann in parsed_data2['labels_info']:
            for box in ann['boxes']:
                x, y, w, h = box
                rect = patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='lightcoral', facecolor='none', linestyle="--")
                ax.add_patch(rect)
    
    # 遍历过滤后的匹配对进行可视化和对比
    for pair in filtered_pairs:
        box1 = pair["box1"]
        box2 = pair["box2"]
        tag = pair["tag"]
        group = pair["global_group"]
        iou = pair["iou"]
        ann1 = pair["ann1"]
        ann2 = pair["ann2"]
        
        # 绘制当前匹配对的框
        x, y, w, h = box1
        rect = patches.Rectangle((x, y), w, h, linewidth=2, edgecolor='blue', facecolor='none')
        ax.add_patch(rect)
        x, y, w, h = box2
        rect = patches.Rectangle((x, y), w, h, linewidth=2, edgecolor='red', facecolor='none')
        ax.add_patch(rect)
        
        # 在框的中心处添加标签（标注 tag 以及全局组号）
        center1 = (box1[0] + box1[2] / 2, box1[1] + box1[3] / 2)
        center2 = (box2[0] + box2[2] / 2, box2[1] + box2[3] / 2)
        # ax.text(center1[0], center1[1], f'{tag} G{group}', color='blue', fontsize=12, backgroundcolor='white')
        # ax.text(center2[0], center2[1], f'{tag} G{group}', color='red', fontsize=12, backgroundcolor='white')
        
        # 对比两标注员的维度值（以维度名称为键构造字典）
        dims1 = {dim["name"]: dim["dimensionValues"] for dim in ann1.get("dimensionValues", []) if dim.get("name")}
        dims2 = {dim["name"]: dim["dimensionValues"] for dim in ann2.get("dimensionValues", []) if dim.get("name")}
        common_dims = set(dims1.keys()).intersection(set(dims2.keys()))
        for dim in common_dims:
            val1 = ", ".join(dims1[dim]) if isinstance(dims1[dim], list) else str(dims1[dim])
            val2 = ", ".join(dims2[dim]) if isinstance(dims2[dim], list) else str(dims2[dim])
            if val1 != val2:
                val1_disp = f"<span style='color:red'>{val1}</span>"
                val2_disp = f"<span style='color:red'>{val2}</span>"
            else:
                val1_disp = val1
                val2_disp = val2
            table_data.append({
                "Group": group,
                "Tag": tag,
                "Dimension": dim,
                "Annotator1": val1_disp,
                "Annotator2": val2_disp,
                "IoU": f"{iou:.2f}"
            })
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.pyplot(fig)
    with col2:
        if table_data:
            df = pd.DataFrame(table_data)
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.write("没有匹配的标注结果。")

    col3, col4 = st.columns([1, 1])
    fig2, ax2 = plt.subplots(figsize=(10, 10))
    ax2.imshow(img)
    ax2.set_title("原始图片")
    with col3:             
        st.pyplot(fig2)
    with col4:
        pass

# ----------------------------
# 主界面逻辑
# ----------------------------
def compare_anno_results():
    # st.set_page_config(layout="wide")
    st.title("标注结果对比")
    st.write("请选择要对比的标注结果：")
    
    # 调试模式控制开关
    debug_mode = st.checkbox("开启调试模式", value=False)
    
    uploaded_file1 = st.file_uploader("上传第一个标注员的标注结果文件", type="txt")
    uploaded_file2 = st.file_uploader("上传第二个标注员的标注结果文件", type="txt")
    
    if uploaded_file1 is not None and uploaded_file2 is not None:
        try:
            rst1 = json.load(uploaded_file1)
            rst2 = json.load(uploaded_file2)
        except Exception as e:
            st.error(f"文件解析失败: {e}")
            return
        
        filter_option = st.selectbox("是否只选择两个标注员都有标注结果的log_id？", ["全部", "仅有两个标注员标注的结果"])
        all_log_ids = [log["id"] for log in rst1]
        if filter_option == "仅有两个标注员标注的结果":
            log_ids2 = {log["id"] for log in rst2}
            all_log_ids = [log_id for log_id in all_log_ids if log_id in log_ids2]
        all_log_ids.sort(key=lambda x: int(x))
        log_id = st.selectbox("选择要对比的标注结果", all_log_ids)
        
        log1_obj = next(log for log in rst1 if log["id"] == log_id)
        log2_obj = next(log for log in rst2 if log["id"] == log_id)       
        
        # 先计算所有匹配对，获得可选的组号，并传入 debug_mode
        matched_pairs_list = compute_matched_pairs(log1_obj, log2_obj, debug=debug_mode)
        available_groups = sorted(set(pair["global_group"] for pair in matched_pairs_list))
        # 构建下拉选项：显示“全部”以及实际存在的组号
        group_options = ["全部"] + [str(g) for g in available_groups]
        selected_group = st.selectbox("选择匹配框组", options=group_options)
        compare_annotations(log1_obj, log2_obj, selected_group, matched_pairs_list)

    else:
        st.write("请上传两个标注员的标注结果文件（txt格式）。")
