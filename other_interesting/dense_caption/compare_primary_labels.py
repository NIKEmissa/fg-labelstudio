#!/usr/bin/env python3
import argparse
import json
import re
import pandas as pd
from collections import Counter

def parse_log(log_data):
    """
    解析单个 log 数据，提取图片、标注框、一级标签及其它信息。
    """
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

def get_primary_result(log):
    """
    从单个 log 中提取一级标签，清洗后去重排序并合并为逗号分隔的字符串。
    """
    parsed = parse_log(log)
    def clean_tag(tag):
        return re.sub(r'\d+$', '', tag) if tag else "UNKNOWN"
    tags = [clean_tag(label.get("tag", "UNKNOWN")) for label in parsed["labels_info"]]
    if tags:
        unique_tags = sorted(set(tags))
        return ",".join(unique_tags)
    else:
        return ""

def compare_primary_labels_overall(rst1, rst2):
    """
    对比两个标注结果文件中的所有 log（按 log id 匹配）。
    生成一个包含 id、结果一、结果二 的表格，并分别统计：
      - 【包含缺失】的一致率（所有记录）
      - 【排除缺失及空白】的一致率（过滤无效数据）
    同时输出一个过滤后的有效数据表格。
    """
    # 构建 id 到 log 的映射
    logs1 = {log["id"]: log for log in rst1}
    logs2 = {log["id"]: log for log in rst2}
    all_ids = sorted(set(logs1.keys()).union(set(logs2.keys())), key=lambda x: int(x))
    
    rows = []
    for id_ in all_ids:
        res1 = get_primary_result(logs1[id_]) if id_ in logs1 else "缺失"
        res2 = get_primary_result(logs2[id_]) if id_ in logs2 else "缺失"
        rows.append({
            "id": id_,
            "结果一": res1,
            "结果二": res2
        })
    
    df = pd.DataFrame(rows)
    
    # 定义高亮函数：当“结果一”与“结果二”不相等时在输出中标识（这里输出时仅添加标记）
    def mark_diff(val1, val2):
        return val1 if val1 == val2 else f"**{val1}**"
    
    # 输出完整对比表
    print("=== 一级标签整体对比结果（包含缺失） ===")
    print(df.to_string(index=False))
    print()
    
    # 统计【包含缺失】一致率
    total_overall = len(df)
    match_overall = (df["结果一"] == df["结果二"]).sum()
    consistency_overall = match_overall / total_overall * 100 if total_overall > 0 else 0
    
    # 统计【排除缺失及空白】一致率：过滤掉结果为"缺失"或空白的记录
    def is_valid(cell):
        if not isinstance(cell, str):
            return False
        cell = cell.strip()
        return cell != "" and cell != "缺失"
    
    valid_mask = df["结果一"].apply(is_valid) & df["结果二"].apply(is_valid)
    df_valid = df[valid_mask]
    total_valid = len(df_valid)
    match_valid = (df_valid["结果一"] == df_valid["结果二"]).sum()
    consistency_valid = match_valid / total_valid * 100 if total_valid > 0 else 0
    
    print(f"【包含缺失】一致率：{consistency_overall:.2f}% （匹配：{match_overall} / 总记录数：{total_overall}）")
    print(f"【排除缺失及空白】一致率：{consistency_valid:.2f}% （匹配：{match_valid} / 有效记录数：{total_valid}）")
    print()
    
    # 输出排除了无效数据后的表格
    if total_valid > 0:
        print("=== 排除无效数据后的对比结果 ===")
        print(df_valid.to_string(index=False))
    else:
        print("没有有效数据用于展示排除无效数据后的结果。")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="一级标签对比脚本")
    parser.add_argument("file1", help="第一个标注结果文件路径")
    parser.add_argument("file2", help="第二个标注结果文件路径")
    args = parser.parse_args()
    
    try:
        with open(args.file1, encoding="utf-8") as f1:
            rst1 = json.load(f1)
    except Exception as e:
        print(f"加载文件 {args.file1} 失败: {e}")
        exit(1)
    
    try:
        with open(args.file2, encoding="utf-8") as f2:
            rst2 = json.load(f2)
    except Exception as e:
        print(f"加载文件 {args.file2} 失败: {e}")
        exit(1)
    
    compare_primary_labels_overall(rst1, rst2)
