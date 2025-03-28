import csv
import os
import requests
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from urllib.parse import urlparse
from tqdm import tqdm

def download_image(url, dest_dir, filename=None):
    """
    根据 URL 下载图片到目标目录，返回下载结果信息。
    """
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()  # 检查响应状态是否正常
        # 若未指定文件名，则从 URL 中提取
        if not filename:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename:  # 若 URL 中无文件名，则使用默认文件名
                filename = "image.jpg"
        dest_path = os.path.join(dest_dir, filename)
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return f"已下载：{url} -> {dest_path}"
    except Exception as e:
        return f"下载 {url} 时出错: {e}"

def download_images_from_csv(csv_file, url_column, dest_dir, max_workers):
    """
    从 CSV 文件中读取指定列的 URL，使用多进程并行下载图片，并显示下载进度条。
    """
    # 如果目标目录不存在，则创建
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    # 读取 CSV 文件中的 URL
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        urls = [row[url_column] for row in reader if row[url_column]]
    
    results = []
    # 使用进程池并行下载图片
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = {executor.submit(download_image, url, dest_dir): url for url in urls}
        # 使用 tqdm 显示进度，总数为任务数量
        for future in tqdm(as_completed(futures), total=len(futures), desc="下载进度"):
            res = future.result()
            print(res)
            results.append(res)
    return results

def main():
    parser = argparse.ArgumentParser(description="根据 CSV 文件指定列的 URL 下载图片")
    parser.add_argument('--csv_file', type=str, required=True, help="CSV 文件路径")
    parser.add_argument('--url_column', type=str, required=True, help="CSV 文件中包含 URL 的列名称")
    parser.add_argument('--dest_dir', type=str, default='downloaded_images', help="图片保存的目标目录，默认为 downloaded_images")
    parser.add_argument('--max_workers', type=int, default=os.cpu_count(), help="并发进程数，默认值为 CPU 核心数")
    
    args = parser.parse_args()
    
    download_images_from_csv(args.csv_file, args.url_column, args.dest_dir, args.max_workers)

if __name__ == '__main__':
    main()
