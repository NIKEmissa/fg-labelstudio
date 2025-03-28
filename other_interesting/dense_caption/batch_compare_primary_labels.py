#!/usr/bin/env python3
import argparse
import os
import json
import re
import pandas as pd

def parse_log(log_data):
    """
    解析单个 log 数据，提取图片、标注框、一级标签等信息。
    这里只解析一级标签，不处理拉框和二级维度。
    """
    log = log_data
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
                "boxes": []  # 此处只提取一级标签
            }
            labels_info.append(label_info)
    
    return {
        "log_info": {"id": log.get("id"), "isInvalid": log.get("isInvalid")},
        "picture_info": picture_info,
        "labels_info": labels_info,
    }

def get_primary_result(log):
    """
    从单个 log 中提取一级标签：去除尾部数字后缀、去重、排序后合并为逗号分隔的字符串。
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

def get_url_result(log):
    """
    从单个 log 中提取所有图片的 URL 信息：
    遍历 pictureList，提取 url 字段，去重、排序后合并为逗号分隔的字符串。
    """
    parsed = parse_log(log)
    urls = [pic.get("url", "").strip() for pic in parsed["picture_info"] if pic.get("url")]
    if urls:
        unique_urls = sorted(set(urls))
        return ",".join(unique_urls)
    else:
        return ""

def compare_primary_labels_for_pair(rst1, rst2):
    """
    对比两个标注结果文件中的所有 log（按 log id 匹配），生成对比表，
    并计算统计数据（仅针对一级标签）：
      - 【包含缺失】：所有记录一致率
      - 【排除缺失及空白】：过滤掉“缺失”或空白记录后的一致率
    同时，每行增加 URL 信息（分别为 url标注员答案 和 url参考答案）。
    返回一个三元组：(stats, df_full, df_valid)。
    """
    # 构建 id 到 log 的映射
    logs1 = {log["id"]: log for log in rst1}
    logs2 = {log["id"]: log for log in rst2}
    all_ids = sorted(set(logs1.keys()).union(set(logs2.keys())), key=lambda x: int(x))
    
    rows = []
    for id_ in all_ids:
        primary1 = get_primary_result(logs1[id_]) if id_ in logs1 else "缺失"
        primary2 = get_primary_result(logs2[id_]) if id_ in logs2 else "缺失"
        url1 = get_url_result(logs1[id_]) if id_ in logs1 else "缺失"
        url2 = get_url_result(logs2[id_]) if id_ in logs2 else "缺失"
        rows.append({
            "id": id_,
            "url": url2,
            "标注员答案": primary1,
            "参考答案": primary2,
            # "url标注员答案": url1,
        })
    df_full = pd.DataFrame(rows)
    
    # 统计【包含缺失】（仅针对一级标签部分）
    total_overall = len(df_full)
    match_overall = (df_full["标注员答案"] == df_full["参考答案"]).sum()
    consistency_overall = match_overall / total_overall * 100 if total_overall > 0 else 0
    
    # 过滤【排除缺失及空白】记录（仅针对一级标签部分）
    def is_valid(cell):
        if not isinstance(cell, str):
            return False
        return cell.strip() != "" and cell.strip() != "缺失"
    
    valid_mask = df_full["标注员答案"].apply(is_valid) & df_full["参考答案"].apply(is_valid)
    df_valid = df_full[valid_mask].copy()
    total_valid = len(df_valid)
    match_valid = (df_valid["标注员答案"] == df_valid["参考答案"]).sum()
    consistency_valid = match_valid / total_valid * 100 if total_valid > 0 else 0
    
    stats = {
        "total_overall": total_overall,
        "match_overall": match_overall,
        "consistency_overall": consistency_overall,
        "total_valid": total_valid,
        "match_valid": match_valid,
        "consistency_valid": consistency_valid
    }
    return stats, df_full, df_valid


def main():
    parser = argparse.ArgumentParser(description="批量一级标签对比并追加统计结果到原CSV，同时保存每对对比结果的表格")
    parser.add_argument("--csv", required=True, help="包含文件对信息的 CSV 文件路径")
    parser.add_argument("--root_dir", required=True, help="文件根目录，所有文件从该目录下查找")
    parser.add_argument("--output", default="batch_compare_result_append.csv", help="输出追加统计结果后的 CSV 文件路径")
    parser.add_argument("--result_dir", default="compare_results", help="保存每行对比结果表格的目录")
    # 指定 CSV 中存放文件名的列名（默认分别为“标注结果”和“答案任务标注结果”）
    parser.add_argument("--col1", default="标注结果", help="CSV 文件中标注结果文件名所在的列名")
    parser.add_argument("--col2", default="答案任务标注结果", help="CSV 文件中答案任务标注结果文件名所在的列名")
    args = parser.parse_args()
    
    # 读取原始 CSV，并删除所有列名中包含 "Unnamed" 的列
    df_csv = pd.read_csv(args.csv)
    df_csv = df_csv.loc[:, ~df_csv.columns.str.contains('^Unnamed')]
    
    # 如果指定的结果目录不存在，则创建之
    if not os.path.exists(args.result_dir):
        os.makedirs(args.result_dir)
    
    stats_list = []
    for idx, row in df_csv.iterrows():
        file1_name = str(row[args.col1]).strip()
        file2_name = str(row[args.col2]).strip()
        file1_path = os.path.join(args.root_dir, file1_name)
        file2_path = os.path.join(args.root_dir, file2_name)
        task1_name = str(row['任务名称']).strip()
        id_name = str(file1_name.strip('.txt') + file2_name.strip('.txt') + task1_name)

        # 初始化统计值，若文件加载失败则使用空值
        current_stats = {
            "总记录数": None,
            "匹配数(包含缺失)": None,
            "一致率(包含缺失)": None,
            "有效记录数": None,
            "匹配数(排除缺失及空白)": None,
            "一致率(排除缺失及空白)": None
        }
        try:
            with open(file1_path, encoding="utf-8") as f1:
                rst1 = json.load(f1)
        except Exception as e:
            print(f"加载文件 {file1_path} 失败: {e}")
            stats_list.append(current_stats)
            continue
        try:
            with open(file2_path, encoding="utf-8") as f2:
                rst2 = json.load(f2)
        except Exception as e:
            print(f"加载文件 {file2_path} 失败: {e}")
            stats_list.append(current_stats)
            continue
        
        stats, df_full, df_valid = compare_primary_labels_for_pair(rst1, rst2)
        current_stats = {
            "总记录数": stats["total_overall"],
            "匹配数(包含缺失)": stats["match_overall"],
            "一致率(包含缺失)": stats["consistency_overall"],
            "有效记录数": stats["total_valid"],
            "匹配数(排除缺失及空白)": stats["match_valid"],
            "一致率(排除缺失及空白)": stats["consistency_valid"]
        }
        stats_list.append(current_stats)
        
        # 对过滤后的表格增加一列“是否一致”
        if not df_valid.empty:
            df_valid["是否一致"] = df_valid.apply(lambda r: "一致" if r["标注员答案"] == r["参考答案"] else "不一致", axis=1)
        
        # 保存两个对比结果表格到 CSV
        # 使用行号构成唯一名称
        full_csv_filename = os.path.join(args.result_dir, f"compare_{id_name}_full.csv")
        valid_csv_filename = os.path.join(args.result_dir, f"compare_{id_name}_valid.csv")
        df_full.to_csv(full_csv_filename, index=False, encoding="utf-8-sig")
        df_valid.to_csv(valid_csv_filename, index=False, encoding="utf-8-sig")
        
        print(f"处理文件对: {file1_name} 和 {file2_name}")
        print(f"【包含缺失】一致率: {stats['consistency_overall']:.2f}% ({stats['match_overall']}/{stats['total_overall']})")
        print(f"【排除缺失及空白】一致率: {stats['consistency_valid']:.2f}% ({stats['match_valid']}/{stats['total_valid']})")
        print(f"保存完整对比表: {full_csv_filename}")
        print(f"保存有效对比表: {valid_csv_filename}")
        print("-" * 40)
    
    # 将统计结果 DataFrame 与原始 CSV 合并（按行追加新列）
    df_stats = pd.DataFrame(stats_list)
    df_new = pd.concat([df_csv, df_stats], axis=1)
    df_new = df_new.loc[:, ~df_new.columns.str.contains('^Unnamed')]
    df_new.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"\n追加统计结果后的 CSV 文件已保存到 {args.output}")

if __name__ == '__main__':
    main()
