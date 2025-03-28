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
# 辅助函数：将二级标签（标签项）的选项值转换为字符串（实际上比较的是三级标签，即选项值）
# ----------------------------
def get_dimension_str(annotation):
    dims = annotation.get("dimensionValues", [])
    dims_str = []
    for dim in dims:
        name = dim.get("name")
        values = dim.get("dimensionValues", [])
        if values:
            clean_values = [str(v) for v in values if v is not None]
            dims_str.append(f"{name}: {', '.join(clean_values)}")
        else:
            dims_str.append(f"{name}: None")
    return "; ".join(dims_str)

# ----------------------------
# 计算两个框的 IoU
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

# ----------------------------
# 解析日志数据
# ----------------------------
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
                            # 将选项值保存到 dimensionValues 中（即三级标签）
                            dimension_info["dimensionValues"].append(value.get("name"))
                    label_info["dimensionValues"].append(dimension_info)
            labels_info.append(label_info)
    
    return {
        "log_info": log_info,
        "picture_info": picture_info,
        "labels_info": labels_info,
    }

# ----------------------------
# 匹配框（支持传入带框 ID 的四元组）
# ----------------------------
def match_boxes(boxes1, boxes2, threshold=0.3, debug=False):
    n1 = len(boxes1)
    n2 = len(boxes2)
    cost_matrix = np.zeros((n1, n2))
    iou_matrix = np.zeros((n1, n2))
    for i, (box1, ann1, tag1, box_id1) in enumerate(boxes1):
        for j, (box2, ann2, tag2, box_id2) in enumerate(boxes2):
            iou = compute_iou(box1, box2)
            cost_matrix[i, j] = 1 - iou
            iou_matrix[i, j] = iou
    if debug:
        st.header("debug: 匹配框iou_matrix")
        st.table(iou_matrix)
    matched_pairs = []
    for i, (box1, ann1, tag1, box_id1) in enumerate(boxes1):
        for j, (box2, ann2, tag2, box_id2) in enumerate(boxes2):
            iou = compute_iou(box1, box2)
            if iou >= threshold:
                matched_pairs.append(((box1, ann1, tag1, box_id1), (box2, ann2, tag2, box_id2), iou))
                if debug:
                    st.write(f"debug: 匹配到框：{box_id1} 与 {box_id2}，IoU = {iou:.2f}")
    return matched_pairs

# ----------------------------
# 为每个框赋予 ID，并返回所有框的匹配信息，同时收集主标签不匹配的混淆对
# ----------------------------
def compute_matched_pairs(log1, log2, threshold=0.3, debug=False):
    import re
    def clean_tag(tag):
        return re.sub(r'\d+$', '', tag) if tag else "UNKNOWN"
    
    parsed_data1 = parse_log(log1)
    parsed_data2 = parse_log(log2)
    
    # 为 Annotator1 分配框ID
    boxes1 = []
    for idx, ann in enumerate(parsed_data1['labels_info']):
        tag = ann.get("tag", "UNKNOWN")
        for i, box in enumerate(ann["boxes"]):
            boxes1.append((box, ann, tag, f"Annotator1_{idx+1}_{i+1}"))
    
    # 为 Annotator2 分配框ID
    boxes2 = []
    for idx, ann in enumerate(parsed_data2['labels_info']):
        tag = ann.get("tag", "UNKNOWN")
        for i, box in enumerate(ann["boxes"]):
            boxes2.append((box, ann, tag, f"Annotator2_{idx+1}_{i+1}"))
            
    # 构造所有框的字典，方便后续根据框ID查找详细信息
    all_boxes = {}
    for (box, ann, tag, box_id) in boxes1:
        all_boxes[box_id] = {
            "Annotator": "Annotator1",
            "Tag": tag,
            "Box": box,
            "Dimensions": get_dimension_str(ann)
        }
    for (box, ann, tag, box_id) in boxes2:
        all_boxes[box_id] = {
            "Annotator": "Annotator2",
            "Tag": tag,
            "Box": box,
            "Dimensions": get_dimension_str(ann)
        }
    
    # Debug：展示提取到的框
    if debug:
        debug_boxes1 = [{"Annotator": "Annotator1", "Tag": item[2], "Box": item[0], "Box ID": item[3]} for item in boxes1]
        debug_boxes2 = [{"Annotator": "Annotator2", "Tag": item[2], "Box": item[0], "Box ID": item[3]} for item in boxes2]
        st.write("### Debug: 从 Annotator1 中提取到的所有框")
        st.dataframe(pd.DataFrame(debug_boxes1))
        st.write("### Debug: 从 Annotator2 中提取到的所有框")
        st.dataframe(pd.DataFrame(debug_boxes2))
    
    # 匹配阶段
    matched_pairs_raw = match_boxes(boxes1, boxes2, threshold=threshold, debug=debug)
    
    matched_pairs_list = []
    confused_primary_pairs = []
    global_group = 0
    used_boxes1 = set()
    used_boxes2 = set()
    for idx, (item1, item2, iou) in enumerate(matched_pairs_raw):
        box1, ann1, tag1, box_id1 = item1
        box2, ann2, tag2, box_id2 = item2
        if clean_tag(tag1) == clean_tag(tag2):
            global_group += 1
            matched_pairs_list.append({
                "global_group": global_group,
                "tag": tag1,
                "pair_index": idx + 1,
                "box1": box1,
                "ann1": ann1,
                "box_id1": box_id1,
                "box2": box2,
                "ann2": ann2,
                "box_id2": box_id2,
                "iou": iou
            })
            used_boxes1.add(box_id1)
            used_boxes2.add(box_id2)
        else:
            confused_primary_pairs.append({
                "box_id1": box_id1,
                "tag1": tag1,
                "box_id2": box_id2,
                "tag2": tag2,
                "iou": iou
            })
            if debug:
                st.write(f"### Debug: 主标签不匹配：{tag1} vs {tag2} (Box {box_id1} vs {box_id2})")
                
    unmatched_boxes1 = [
        {
            "Annotator": "Annotator1",
            "Tag": tag,
            "Box": box,
            "Box ID": box_id,
            "Dimensions": get_dimension_str(ann)
        } for (box, ann, tag, box_id) in boxes1 if box_id not in used_boxes1
    ]
    unmatched_boxes2 = [
        {
            "Annotator": "Annotator2",
            "Tag": tag,
            "Box": box,
            "Box ID": box_id,
            "Dimensions": get_dimension_str(ann)
        } for (box, ann, tag, box_id) in boxes2 if box_id not in used_boxes2
    ]
    
    return {
        "matched_pairs": matched_pairs_list,
        "confused_primary_pairs": confused_primary_pairs,
        "unmatched_boxes1": unmatched_boxes1,
        "unmatched_boxes2": unmatched_boxes2,
        "all_box_ids": list(all_boxes.keys()),
        "all_boxes": all_boxes
    }

# ----------------------------
# 统计分析函数：计算整体对比指标（单图级）
# ----------------------------
def compute_statistics(log1, log2, result):
    stats = {}
    # 总框数统计
    total_boxes_annotator1 = sum(1 for box in result["all_boxes"].values() if box["Annotator"]=="Annotator1")
    total_boxes_annotator2 = sum(1 for box in result["all_boxes"].values() if box["Annotator"]=="Annotator2")
    stats["total_boxes_annotator1"] = total_boxes_annotator1
    stats["total_boxes_annotator2"] = total_boxes_annotator2

    # 平均 IoU（仅基于匹配对）
    matched_pairs = result["matched_pairs"]
    if matched_pairs:
         avg_iou = sum(pair["iou"] for pair in matched_pairs) / len(matched_pairs)
    else:
         avg_iou = 0
    stats["average_iou"] = avg_iou

    # 一级标签匹配率：匹配的框（每对两个框）占总框数比例
    matched_boxes_count = len(matched_pairs) * 2
    total_boxes = total_boxes_annotator1 + total_boxes_annotator2
    primary_matching_rate = matched_boxes_count / total_boxes if total_boxes > 0 else 0
    stats["primary_matching_rate"] = primary_matching_rate

    # 一级标签混淆统计：基于 IoU 大于阈值但主标签不一致的匹配对
    confused_primary = result.get("confused_primary_pairs", [])
    confusion_dict = {}
    for pair in confused_primary:
         key = (pair["tag1"], pair["tag2"])
         confusion_dict[key] = confusion_dict.get(key, 0) + 1
    sorted_primary_confusion = sorted(confusion_dict.items(), key=lambda x: x[1], reverse=True)
    stats["primary_confusion"] = sorted_primary_confusion

    # 三级标签（即各选项值）的匹配分析
    def get_dims_dict(ann):
         dims = {}
         for dim in ann.get("dimensionValues", []):
             name = dim.get("name")
             if name:
                 # 直接取保存的选项值列表（即三级标签），用逗号连接
                 values = [str(v) for v in dim.get("dimensionValues", []) if v is not None]
                 dims[name] = ", ".join(values)
         return dims

    tertiary_match_count = 0
    tertiary_total_count = 0
    tertiary_confusion = {}  # key: (维度名称, annotator1选项, annotator2选项)
    option_stats = {}  # 记录各选项详细匹配情况
    for pair in matched_pairs:
         dims1 = get_dims_dict(pair["ann1"])
         dims2 = get_dims_dict(pair["ann2"])
         common_dims = set(dims1.keys()).intersection(set(dims2.keys()))
         for dim in common_dims:
              val1 = dims1[dim]
              val2 = dims2[dim]
              tertiary_total_count += 1
              option_stats.setdefault(dim, {"match": 0, "total": 0})
              option_stats[dim]["total"] += 1
              if val1 == val2:
                  tertiary_match_count += 1
                  option_stats[dim]["match"] += 1
              else:
                  key = (dim, val1, val2)
                  tertiary_confusion[key] = tertiary_confusion.get(key, 0) + 1
    tertiary_matching_rate = tertiary_match_count / tertiary_total_count if tertiary_total_count > 0 else 0
    stats["tertiary_matching_rate"] = tertiary_matching_rate
    stats["tertiary_confusion"] = sorted(tertiary_confusion.items(), key=lambda x: x[1], reverse=True)
    stats["option_stats"] = option_stats

    return stats

# ----------------------------
# 整体对比分析函数：统计两个文件中所有匹配 log 的总体指标
# ----------------------------
def overall_comparison_analysis(rst1, rst2, debug_mode=False):
    # 聚合变量
    agg_total_boxes_annotator1 = 0
    agg_total_boxes_annotator2 = 0
    agg_sum_iou = 0
    agg_count_iou = 0
    agg_primary_matched_boxes = 0
    agg_total_boxes = 0
    agg_tertiary_match_count = 0
    agg_tertiary_total = 0
    overall_primary_confusion = {}
    overall_tertiary_confusion = {}
    overall_option_stats = {}
    total_pairs_count = 0

    # 辅助函数：提取选项值字典
    def get_dims_dict(ann):
         dims = {}
         for dim in ann.get("dimensionValues", []):
             name = dim.get("name")
             if name:
                 values = [str(v) for v in dim.get("dimensionValues", []) if v is not None]
                 dims[name] = ", ".join(values)
         return dims

    # 构造匹配对列表：遍历两个文件，依据图片 URL 进行匹配
    matching_pairs_overall = []
    for log1 in rst1:
         if "pictureList" not in log1 or not log1["pictureList"]:
              continue
         url1 = log1["pictureList"][0].get("url", "")
         for log2 in rst2:
             if "pictureList" not in log2 or not log2["pictureList"]:
                 continue
             url2 = log2["pictureList"][0].get("url", "")
             if url1 == url2:
                 matching_pairs_overall.append((log1, log2))
    # 遍历所有匹配对
    for log1, log2 in matching_pairs_overall:
         total_pairs_count += 1
         result = compute_matched_pairs(log1, log2, debug=debug_mode)
         # 统计各标注员框数
         boxes1 = sum(1 for box in result["all_boxes"].values() if box["Annotator"]=="Annotator1")
         boxes2 = sum(1 for box in result["all_boxes"].values() if box["Annotator"]=="Annotator2")
         agg_total_boxes_annotator1 += boxes1
         agg_total_boxes_annotator2 += boxes2
         agg_total_boxes += (boxes1 + boxes2)
         # 匹配对统计
         matched_pairs = result["matched_pairs"]
         for pair in matched_pairs:
             agg_sum_iou += pair["iou"]
             agg_count_iou += 1
         agg_primary_matched_boxes += len(matched_pairs) * 2
         # 主标签混淆
         for cp in result.get("confused_primary_pairs", []):
             key = (cp["tag1"], cp["tag2"])
             overall_primary_confusion[key] = overall_primary_confusion.get(key, 0) + 1
         # 三级标签（选项值）匹配统计
         for pair in matched_pairs:
             dims1 = get_dims_dict(pair["ann1"])
             dims2 = get_dims_dict(pair["ann2"])
             common_dims = set(dims1.keys()).intersection(set(dims2.keys()))
             for dim in common_dims:
                 agg_tertiary_total += 1
                 overall_option_stats.setdefault(dim, {"match": 0, "total": 0})
                 overall_option_stats[dim]["total"] += 1
                 if dims1[dim] == dims2[dim]:
                     agg_tertiary_match_count += 1
                     overall_option_stats[dim]["match"] += 1
                 else:
                     key = (dim, dims1[dim], dims2[dim])
                     overall_tertiary_confusion[key] = overall_tertiary_confusion.get(key, 0) + 1

    overall_avg_iou = agg_sum_iou / agg_count_iou if agg_count_iou > 0 else 0
    overall_primary_matching_rate = agg_primary_matched_boxes / agg_total_boxes if agg_total_boxes > 0 else 0
    overall_tertiary_matching_rate = agg_tertiary_match_count / agg_tertiary_total if agg_tertiary_total > 0 else 0

    aggregated_stats = {
         "total_pairs": total_pairs_count,
         "total_boxes_annotator1": agg_total_boxes_annotator1,
         "total_boxes_annotator2": agg_total_boxes_annotator2,
         "average_iou": overall_avg_iou,
         "primary_matching_rate": overall_primary_matching_rate,
         "tertiary_matching_rate": overall_tertiary_matching_rate,
         "primary_confusion": sorted(overall_primary_confusion.items(), key=lambda x: x[1], reverse=True),
         "tertiary_confusion": sorted(overall_tertiary_confusion.items(), key=lambda x: x[1], reverse=True),
         "option_stats": overall_option_stats
    }
    return aggregated_stats

# ----------------------------
# 对比标注结果并绘制可视化（已修改颜色）
# ----------------------------
def compare_annotations(log1, log2, selected_group, selected_box_ids, 
                        matched_pairs_list, all_boxes, group_filter_type, 
                        unmatched_boxes, show_box_names, is_box_id_filter=False):
    # 加载图片（取第一个图片）
    parsed_data1 = parse_log(log1)
    if len(parsed_data1['picture_info']) == 0:
        st.error("无图片信息")
        return
    img_url = parsed_data1['picture_info'][0]['url']
    try:
        with st.spinner("还在刷新中..."):
            response = requests.get(img_url)
            img = Image.open(BytesIO(response.content))
    except Exception as e:
        st.error(f"图片下载失败: {e}")
        return

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(img)
    ax.set_title("标注对比")
    
    table_data = []
    
    if group_filter_type == "all":
        # 绘制所有匹配对和未匹配框
        for pair in matched_pairs_list:
            box1 = pair["box1"]
            box2 = pair["box2"]
            tag = pair["tag"]
            group = pair["global_group"]
            iou = pair["iou"]
            ann1 = pair["ann1"]
            ann2 = pair["ann2"]
            
            # 修改颜色：Annotator1 使用粉色，Annotator2 使用蓝色
            rect1 = patches.Rectangle((box1[0], box1[1]), box1[2], box1[3],
                                      linewidth=2, edgecolor='pink', facecolor='none')
            rect2 = patches.Rectangle((box2[0], box2[1]), box2[2], box2[3],
                                      linewidth=2, edgecolor='blue', facecolor='none')
            ax.add_patch(rect1)
            ax.add_patch(rect2)
            if show_box_names:
                ax.text(box1[0], box1[1], pair["box_id1"], color='pink', fontsize=10, backgroundcolor='none')
                ax.text(box2[0], box2[1], pair["box_id2"], color='blue', fontsize=10, backgroundcolor='none')
            
            dims1 = {dim["name"]: [str(v) for v in dim.get("dimensionValues", []) if v is not None] 
                     for dim in ann1.get("dimensionValues", []) if dim.get("name")}
            dims2 = {dim["name"]: [str(v) for v in dim.get("dimensionValues", []) if v is not None] 
                     for dim in ann2.get("dimensionValues", []) if dim.get("name")}
            common_dims = set(dims1.keys()).intersection(set(dims2.keys()))
            for dim in common_dims:
                val1 = ", ".join(dims1[dim])
                val2 = ", ".join(dims2[dim])
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
        
        for box_info in unmatched_boxes:
            box = box_info["Box"]
            color = 'pink' if box_info["Annotator"] == "Annotator1" else 'blue'
            rect = patches.Rectangle((box[0], box[1]), box[2], box[3],
                                     linewidth=2, edgecolor=color, facecolor='none', linestyle='--')
            ax.add_patch(rect)
            if show_box_names:
                ax.text(box[0], box[1], box_info["Box ID"], color=color, fontsize=10, backgroundcolor='none')
            table_data.append({
                "Group": "-",
                "Tag": box_info["Tag"],
                "Dimension": box_info["Dimensions"],
                "Annotator1": box_info["Annotator"] if box_info["Annotator"]=="Annotator1" else "",
                "Annotator2": box_info["Annotator"] if box_info["Annotator"]=="Annotator2" else "",
                "IoU": "-"
            })
    
    elif group_filter_type == "matched":
        if is_box_id_filter and not selected_box_ids:
            filtered_pairs = []
            individual_box_ids = set()
        else:
            filtered_pairs = matched_pairs_list
            if selected_group != "全部":
                try:
                    group_id = int(selected_group)
                    filtered_pairs = [pair for pair in filtered_pairs if pair["global_group"] == group_id]
                except Exception as e:
                    st.error("选择的匹配组无效")
                    return
            if selected_box_ids:
                filtered_pairs = [
                    pair for pair in filtered_pairs 
                    if (pair["box_id1"] in selected_box_ids and pair["box_id2"] in selected_box_ids)
                ]
            individual_box_ids = set(selected_box_ids) if selected_box_ids else set()
            for pair in filtered_pairs:
                individual_box_ids.discard(pair["box_id1"])
                individual_box_ids.discard(pair["box_id2"])
        
        for pair in filtered_pairs:
            box1 = pair["box1"]
            box2 = pair["box2"]
            tag = pair["tag"]
            group = pair["global_group"]
            iou = pair["iou"]
            ann1 = pair["ann1"]
            ann2 = pair["ann2"]
            
            rect1 = patches.Rectangle((box1[0], box1[1]), box1[2], box1[3],
                                      linewidth=2, edgecolor='pink', facecolor='none')
            rect2 = patches.Rectangle((box2[0], box2[1]), box2[2], box2[3],
                                      linewidth=2, edgecolor='blue', facecolor='none')
            ax.add_patch(rect1)
            ax.add_patch(rect2)
            if show_box_names:
                ax.text(box1[0], box1[1], pair["box_id1"], color='pink', fontsize=10, backgroundcolor='none')
                ax.text(box2[0], box2[1], pair["box_id2"], color='blue', fontsize=10, backgroundcolor='none')
            
            dims1 = {dim["name"]: [str(v) for v in dim.get("dimensionValues", []) if v is not None] 
                     for dim in ann1.get("dimensionValues", []) if dim.get("name")}
            dims2 = {dim["name"]: [str(v) for v in dim.get("dimensionValues", []) if v is not None] 
                     for dim in ann2.get("dimensionValues", []) if dim.get("name")}
            common_dims = set(dims1.keys()).intersection(set(dims2.keys()))
            for dim in common_dims:
                val1 = ", ".join(dims1[dim])
                val2 = ", ".join(dims2[dim])
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
        
        for box_id in individual_box_ids:
            box_info = all_boxes.get(box_id)
            if box_info:
                box = box_info["Box"]
                color = "pink" if box_info["Annotator"] == "Annotator1" else "blue"
                rect = patches.Rectangle((box[0], box[1]), box[2], box[3],
                                         linewidth=2, edgecolor=color, facecolor='none', linestyle='--')
                ax.add_patch(rect)
                if show_box_names:
                    ax.text(box[0], box[1], box_id, color=color, fontsize=10, backgroundcolor='none')
                table_data.append({
                    "Group": "-",
                    "Tag": box_info["Tag"],
                    "Dimension": box_info["Dimensions"],
                    "Annotator1": box_info["Annotator"] if box_info["Annotator"]=="Annotator1" else "",
                    "Annotator2": box_info["Annotator"] if box_info["Annotator"]=="Annotator2" else "",
                    "IoU": "-"
                })
    
    elif group_filter_type == "unmatched":
        if selected_box_ids:
            unmatched_filtered = [box for box in unmatched_boxes if box["Box ID"] in selected_box_ids]
        else:
            unmatched_filtered = unmatched_boxes
        for box_info in unmatched_filtered:
            box = box_info["Box"]
            color = "pink" if box_info["Annotator"] == "Annotator1" else "blue"
            rect = patches.Rectangle((box[0], box[1]), box[2], box[3],
                                     linewidth=2, edgecolor=color, facecolor='none', linestyle='--')
            ax.add_patch(rect)
            if show_box_names:
                ax.text(box[0], box[1], box_info["Box ID"], color=color, fontsize=10, backgroundcolor='none')
            table_data.append({
                "Group": "-",
                "Tag": box_info["Tag"],
                "Dimension": box_info["Dimensions"],
                "Annotator1": box_info["Annotator"] if box_info["Annotator"]=="Annotator1" else "",
                "Annotator2": box_info["Annotator"] if box_info["Annotator"]=="Annotator2" else "",
                "IoU": "-"
            })
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.pyplot(fig)
    with col2:
        if table_data:
            df = pd.DataFrame(table_data)
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.write("没有匹配或单独选中的标注结果。")
    
    # 显示原始图片作为参考
    fig2, ax2 = plt.subplots(figsize=(10, 10))
    ax2.imshow(img)
    ax2.set_title("原始图片")
    st.pyplot(fig2)

# ----------------------------
# 主函数：上传文件、参数设置、统计分析并调用对比函数
# ----------------------------
def compare_anno_results():
    st.title("标注结果对比")
    
    # 文件上传区域：两列布局
    col_file1, col_file2 = st.columns(2)
    with col_file1:
        uploaded_file1 = st.file_uploader("上传标注员1结果", type="txt")
    with col_file2:
        uploaded_file2 = st.file_uploader("上传标注员2结果", type="txt")
    
    # 参数设置区域：使用 expander 展开，紧凑布局
    with st.expander("参数设置", expanded=True):
        col_params1, col_params2 = st.columns(2)
        with col_params1:
            debug_mode = st.checkbox("开启调试模式", value=False)
            show_box_names = st.checkbox("显示框名", value=False)
        with col_params2:
            filter_option = st.selectbox("log_id 筛选", ["全部", "仅有两个标注员标注的结果"])
            filter_method = st.radio("过滤方式", ["全部", "按匹配组过滤", "按框ID过滤"])
            if filter_method == "按匹配组过滤":
                group_filter_option = st.radio("匹配组类型", ["全部匹配上的框组", "没有匹配上的框组"])
            else:
                group_filter_option = None

    if uploaded_file1 and uploaded_file2:
        try:
            rst1 = json.load(uploaded_file1)
            rst2 = json.load(uploaded_file2)
        except Exception as e:
            st.error(f"文件解析失败: {e}")
            return

        # 使用图片 URL 来匹配两个标注结果（单图对比）
        matching_pairs = []
        for log1 in rst1:
            if "pictureList" not in log1 or not log1["pictureList"]:
                continue
            url1 = log1["pictureList"][0].get("url", "")
            for log2 in rst2:
                if "pictureList" not in log2 or not log2["pictureList"]:
                    continue
                url2 = log2["pictureList"][0].get("url", "")
                if url1 == url2:
                    image_filename = url1.split("/")[-1] if url1 else "unknown"
                    selection_key = f"{log1['id']}_{log2['id']}_{image_filename}"
                    matching_pairs.append((selection_key, log1, log2))

        if not matching_pairs:
            st.error("没有匹配到相同图片的标注结果")
            return

        matching_pairs.sort(key=lambda x: x[0])
        selected_key = st.selectbox("选择要对比的标注结果", [mp[0] for mp in matching_pairs])
        selected_pair = next((mp for mp in matching_pairs if mp[0] == selected_key), None)
        if selected_pair:
            log1_obj = selected_pair[1]
            log2_obj = selected_pair[2]
        else:
            st.error("选择的标注结果无效")
            return

        result = compute_matched_pairs(log1_obj, log2_obj, debug=debug_mode)
        matched_pairs_list = result["matched_pairs"]
        all_box_ids = result["all_box_ids"]
        all_boxes = result["all_boxes"]
        # 合并未匹配框
        unmatched_boxes = result["unmatched_boxes1"] + result["unmatched_boxes2"]

        # 单图统计分析
        stats = compute_statistics(log1_obj, log2_obj, result)
        with st.expander("单图统计分析", expanded=False):
            st.subheader("总体统计")
            st.write(f"**标注员1 总框数：** {stats['total_boxes_annotator1']}")
            st.write(f"**标注员2 总框数：** {stats['total_boxes_annotator2']}")
            st.write(f"**匹配框平均 IoU：** {stats['average_iou']:.2f}")
            st.write(f"**一级标签匹配率：** {stats['primary_matching_rate']*100:.1f}%")
            st.write(f"**三级标签匹配率：** {stats['tertiary_matching_rate']*100:.1f}%")
            
            st.subheader("一级标签混淆情况")
            if stats["primary_confusion"]:
                df_primary = pd.DataFrame([{"Annotator1标签": k[0], "Annotator2标签": k[1], "次数": v} 
                                            for k, v in stats["primary_confusion"]])
                st.dataframe(df_primary)
            else:
                st.write("无一级标签混淆情况。")
            
            st.subheader("三级标签混淆情况")
            if stats["tertiary_confusion"]:
                df_tertiary = pd.DataFrame([{"维度": k[0], "Annotator1选项": k[1], "Annotator2选项": k[2], "次数": v} 
                                             for k, v in stats["tertiary_confusion"]])
                st.dataframe(df_tertiary)
            else:
                st.write("无三级标签混淆情况。")
            
            st.subheader("各选项详细匹配情况")
            if stats["option_stats"]:
                df_option = pd.DataFrame([{"维度": dim, 
                                           "匹配数": v["match"], 
                                           "总比较数": v["total"],
                                           "匹配率": f"{(v['match']/v['total'])*100:.1f}%"}
                                       for dim, v in stats["option_stats"].items()])
                st.dataframe(df_option)
            else:
                st.write("无三级标签数据。")
        
        # 根据用户选择的过滤方式构造参数（保持原逻辑，其余部分无需修改）
        if filter_method == "按框ID过滤":
            group_filter_type = "matched"  # 使用匹配对显示
            selected_box_ids = st.multiselect("选择框ID（格式: AnnotatorX_Y，多选）", options=all_box_ids)
            selected_group = "全部"
            is_box_id_filter = True
        else:
            is_box_id_filter = False
            if filter_method == "按匹配组过滤":
                if group_filter_option == "全部匹配上的框组":
                    group_filter_type = "matched"
                    available_groups = sorted(set(pair["global_group"] for pair in matched_pairs_list))
                    selected_group = st.selectbox("选择匹配组", options=["全部"] + [str(g) for g in available_groups])
                    selected_box_ids = []
                else:
                    group_filter_type = "unmatched"
                    selected_group = "none"
                    selected_box_ids = []
            else:  # 选择“全部”
                group_filter_type = "all"
                selected_group = "全部"
                selected_box_ids = []

        compare_annotations(
            log1_obj, log2_obj, selected_group, selected_box_ids,
            matched_pairs_list, all_boxes, group_filter_type,
            unmatched_boxes, show_box_names, is_box_id_filter
        )
        
        # ----------------------------
        # 整体对比分析（针对两个文件所有 log 的汇总统计）
        # ----------------------------
        with st.expander("所有 log 的整体对比分析", expanded=False):
            st.subheader("整体统计分析")
            overall_stats = overall_comparison_analysis(rst1, rst2, debug_mode)
            st.write(f"**匹配对总数：** {overall_stats['total_pairs']}")
            st.write(f"**标注员1 总框数：** {overall_stats['total_boxes_annotator1']}")
            st.write(f"**标注员2 总框数：** {overall_stats['total_boxes_annotator2']}")
            st.write(f"**匹配框平均 IoU：** {overall_stats['average_iou']:.2f}")
            st.write(f"**一级标签匹配率：** {overall_stats['primary_matching_rate']*100:.1f}%")
            st.write(f"**三级标签匹配率：** {overall_stats['tertiary_matching_rate']*100:.1f}%")
            
            st.subheader("一级标签混淆情况")
            if overall_stats["primary_confusion"]:
                df_primary_all = pd.DataFrame([{"Annotator1标签": k[0], "Annotator2标签": k[1], "次数": v} 
                                            for k, v in overall_stats["primary_confusion"]])
                st.dataframe(df_primary_all)
            else:
                st.write("无一级标签混淆情况。")
            
            st.subheader("三级标签混淆情况")
            if overall_stats["tertiary_confusion"]:
                df_tertiary_all = pd.DataFrame([{"维度": k[0], "Annotator1选项": k[1], "Annotator2选项": k[2], "次数": v} 
                                             for k, v in overall_stats["tertiary_confusion"]])
                st.dataframe(df_tertiary_all)
            else:
                st.write("无三级标签混淆情况。")
            
            st.subheader("各选项详细匹配情况")
            if overall_stats["option_stats"]:
                df_option_all = pd.DataFrame([{"维度": dim, 
                                               "匹配数": v["match"], 
                                               "总比较数": v["total"],
                                               "匹配率": f"{(v['match']/v['total'])*100:.1f}%"}
                                           for dim, v in overall_stats["option_stats"].items()])
                st.dataframe(df_option_all)
            else:
                st.write("无三级标签数据。")
    else:
        st.write("请上传两个标注员的标注结果文件（txt格式）。")

# 调用主函数
if __name__ == "__main__":
    compare_anno_results()
