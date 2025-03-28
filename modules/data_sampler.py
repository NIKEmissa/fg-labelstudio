import os
import json
import hashlib
import pandas as pd
import numpy as np
import streamlit as st
from tqdm import tqdm

def compute_md5(file_path):
    """
    计算指定文件的 MD5 值，用于缓存判断
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
    except Exception as e:
        st.error(f"读取文件计算 MD5 失败: {e}")
    return hash_md5.hexdigest()

def get_unique_values(df, col):
    """
    将指定列中的 NaN 去除，确保为字符串，
    按逗号分割后展开，再去除空白，返回唯一标签列表。
    """
    unique_vals = pd.unique(
        df[col].dropna().astype(str)
              .str.split(',')
              .explode()
              .str.strip()
    )
    return unique_vals.tolist()

def get_cached_unique_tags(csv_file_path, df, columns, cache_file="data_sampler_cache.json"):
    """
    根据 CSV 文件的 MD5 值，尝试从本地缓存中读取指定 columns 的唯一标签值，
    如果缓存不存在或 CSV 已更新，则重新计算并保存到缓存文件中。
    返回一个字典： {列名: [唯一标签值列表, ...], ...}
    """
    csv_md5 = compute_md5(csv_file_path)
    cache = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception as e:
            st.error(f"加载缓存失败: {e}")
            cache = {}
    if csv_md5 in cache:
        return cache[csv_md5]
    else:
        result = {}
        for col in columns:
            result[col] = get_unique_values(df, col)
        cache[csv_md5] = result
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=4)
        except Exception as e:
            st.error(f"写入缓存失败: {e}")
        return result

def sample_by_target(df, target_column, sample_size, url_column="url", random_state=42, selected_tag_values=None):
    """
    针对单个标签组（即 DataFrame 中的一列），提取标签数据（支持逗号分隔的多标签），
    若提供 selected_tag_values，则仅保留在该列表中的标签，
    对每个 (标签组, 标签值) 分组进行随机抽样，返回新 DataFrame，包含“索引”、“标签组”、“标签值”、“URL”四列。
    """
    records = []
    st.write(f"开始处理标签组: {target_column}")
    for idx, row in tqdm(df.iterrows(), total=len(df), desc=f"处理 {target_column} 行", leave=False):
        cell_value = row.get(target_column)
        if isinstance(cell_value, str):
            tags = [tag.strip() for tag in cell_value.split(',') if tag.strip()]
            # 若指定了标签值过滤，则只保留选中的标签
            if selected_tag_values:
                tags = [tag for tag in tags if tag in selected_tag_values]
            for tag in tags:
                records.append({
                    "原索引": idx,
                    "标签组": target_column,
                    "标签值": tag,
                    "URL": row.get(url_column)
                })
    st.write(f"标签组 '{target_column}' 处理完成, 当前记录数: {len(records)}")
    
    records_df = pd.DataFrame(records)
    st.write(f"标签组 '{target_column}' 数据提取完成，共计 {len(records_df)} 条记录")
    
    sampled_records = []
    grouped = records_df.groupby(["标签组", "标签值"])
    grouped_list = list(grouped)
    st.write(f"标签组 '{target_column}' 分组抽样开始，共有 {len(grouped_list)} 个分组")
    
    for (tag_group, tag_value), group in tqdm(grouped_list, total=len(grouped_list), desc=f"分组抽样 {target_column}", leave=False):
        if len(group) >= sample_size:
            sampled = group.sample(n=sample_size, random_state=random_state)
        else:
            sampled = group.copy()
        sampled_records.append(sampled)
    
    if sampled_records:
        final_df = pd.concat(sampled_records, ignore_index=True)
    else:
        final_df = pd.DataFrame(columns=["原索引", "标签组", "标签值", "URL"])
    
    final_df.insert(0, "索引", range(1, len(final_df) + 1))
    st.write(f"标签组 '{target_column}' 最终抽样完成，共计 {len(final_df)} 条记录")
    return final_df

def sample_and_get_all(df, target_columns, sample_size, url_column="url", random_state=42, selected_tag_values=None):
    """
    针对 target_columns 中的每个列，进行数据抽样处理，
    返回一个字典，键为标签组名称，值为对应抽样后的 DataFrame。
    """
    results = {}
    for target in target_columns:
        final_df = sample_by_target(df, target, sample_size, url_column=url_column, random_state=random_state, selected_tag_values=selected_tag_values)
        results[target] = final_df
    return results

@st.fragment
def render_results_fragment(results):
    """
    使用 fragment 渲染抽样结果区域，只更新该部分内容，
    包括下载按钮等内容。
    """
    st.success("抽样完成！请点击下方下载按钮获取结果文件。")
    for target, result_df in results.items():
        csv_data = result_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label=f"下载 {target} 样本",
            data=csv_data,
            file_name=f"{target}_sampled.csv",
            mime="text/csv"
        )

def run_data_sampler():
    st.title("数据抽样工具")
    st.write("本工具将直接从硬编码的 CSV 文件中读取数据进行标签抽样处理，并提供下载抽样结果的功能。")
    
    # 固定 CSV 文件路径
    csv_file_path = '/data1/code/dengxinzhe/sources/query_fg11-fg13_merged_20240605_cn.csv'
    try:
        df = pd.read_csv(csv_file_path)
    except Exception as e:
        st.error(f"读取 CSV 文件失败: {e}")
        return

    # 根据过滤条件筛选数据，例如过滤 'category' 列
    category = st.text_input("请输入过滤类别（例如：连衣裙，不填写则不过滤）", value="连衣裙")
    if category:
        df = df[df['category'] == category]
    
    # 读取映射表文件，获取支持的标签（取“中文”列）
    mapping_file_path = '/data1/code/dengxinzhe/sources/翻译推理 和 专家核验 记录表 - Title 映射表.csv'
    try:
        mapping_df = pd.read_csv(mapping_file_path)
        # 假设映射表中的中文列标题为“中文”
        supported_labels = mapping_df["中文"].dropna().unique().tolist()
    except Exception as e:
        st.error(f"读取映射表失败: {e}")
        supported_labels = []
    
    # 仅保留同时存在于映射表和当前 CSV 表头中的标签
    available_labels = [col for col in df.columns if col in supported_labels]
    if not available_labels:
        st.error("当前 CSV 表头中没有与映射表支持的标签匹配的字段。")
        return
    
    st.write("请选择需要抽样的标签组（仅显示映射表中支持且在 CSV 表头存在的字段）：")
    target_columns = st.multiselect("请选择标签组", options=available_labels, default=available_labels[:2])
    if not target_columns:
        st.warning("请至少选择一个标签组")
        return

    # 利用缓存逻辑提取所有可选标签值（基于 CSV 文件与所有支持的列）
    cached_unique_tags = get_cached_unique_tags(csv_file_path, df, available_labels)
    unique_tags = set()
    # 仅合并用户选择的标签组对应的唯一标签值
    for col in target_columns:
        unique_tags.update(cached_unique_tags.get(col, []))
    unique_tags = sorted(list(unique_tags))
    
    st.write("请选择需要处理的标签值（仅处理所选标签值）：")
    selected_tag_values = st.multiselect("请选择标签值", options=unique_tags, default=unique_tags)
    
    sample_size = st.number_input("每个标签抽样数", min_value=1, value=50)
    
    if st.button("开始抽样"):
        try:
            results = sample_and_get_all(df, target_columns, sample_size, selected_tag_values=selected_tag_values)
            render_results_fragment(results)
        except Exception as e:
            st.error(f"抽样过程中发生错误: {e}")

if __name__ == "__main__":
    run_data_sampler()
