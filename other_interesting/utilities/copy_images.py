import os
import shutil
import pandas as pd
import argparse

def main():
    # 构建命令行参数解析器，描述脚本用途
    parser = argparse.ArgumentParser(
        description="从 CSV 文件指定的列中读取图片路径，并将图片复制到目标文件夹"
    )
    # 第一个参数：CSV 文件路径
    parser.add_argument("csv_file", help="CSV 文件路径")
    # 第二个参数：CSV 中包含图片路径的列名
    parser.add_argument("column", help="CSV 中包含图片路径的列名")
    # 第三个参数：目标文件夹路径，复制后的图片将存放在此文件夹中
    parser.add_argument("dest_folder", help="目标文件夹路径")

    args = parser.parse_args()

    # 检查 CSV 文件是否存在
    if not os.path.exists(args.csv_file):
        print(f"错误：找不到 CSV 文件：{args.csv_file}")
        return

    # 如果目标文件夹不存在则创建
    if not os.path.exists(args.dest_folder):
        os.makedirs(args.dest_folder)
        print(f"创建目标文件夹：{args.dest_folder}")

    # 使用 pandas 读取 CSV 文件
    try:
        df = pd.read_csv(args.csv_file)
    except Exception as e:
        print(f"读取 CSV 文件失败：{e}")
        return

    # 检查指定的列是否在 CSV 中存在
    if args.column not in df.columns:
        print(f"错误：CSV 文件中不存在列：{args.column}")
        return

    # 遍历 CSV 每一行，并复制存在的图片文件到目标文件夹
    for index, row in df.iterrows():
        img_path = row[args.column]
        # 检查路径是否存在，以及是否为文件（避免目录等情况）
        if pd.isna(img_path) or not isinstance(img_path, str):
            print(f"第 {index} 行：图片路径无效。")
            continue

        if os.path.isfile(img_path):
            try:
                shutil.copy2(img_path, args.dest_folder)
                print(f"成功复制：{img_path}")
            except Exception as e:
                print(f"复制失败 {img_path}：{e}")
        else:
            print(f"文件不存在：{img_path}")

if __name__ == "__main__":
    main()
