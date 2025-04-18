import csv
import os
import requests
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
from urllib.parse import urlparse
from tqdm import tqdm

def get_filename(url):
    """
    从 URL 中提取文件名，若无法提取则返回默认文件名 "image.jpg"。
    """
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    if not filename:
        filename = "image.jpg"
    return filename

def check_task(url, dest_dir):
    """
    检查目标目录中是否已存在该 URL 对应的文件（非空则视为已下载）。
    返回三元组 (url, skip_flag, message)：
      - skip_flag 为 True 表示文件存在，应跳过此任务；
      - message 为提示信息（仅在 verbose 模式下打印）。
    """
    filename = get_filename(url)
    dest_path = os.path.join(dest_dir, filename)
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return (url, True, f"跳过已存在的文件：{dest_path}")
    else:
        return (url, False, "")

def download_image(url, dest_dir, filename=None, check_during=False):
    """
    根据 URL 下载图片到目标目录。
    若 check_during 为 True，则在下载前检查文件是否已存在，若存在则直接返回跳过结果。
    返回一个包含下载状态和信息的字典。
    """
    if check_during:
        if not filename:
            filename = get_filename(url)
        dest_path = os.path.join(dest_dir, filename)
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
            return {"url": url, "dest": dest_path, "status": "skipped",
                    "message": f"跳过已存在的文件：{dest_path}"}
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()  # 检查响应状态是否正常
        if not filename:
            filename = get_filename(url)
        dest_path = os.path.join(dest_dir, filename)
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return {"url": url, "dest": dest_path, "status": "success",
                "message": f"已下载：{url} -> {dest_path}"}
    except Exception as e:
        return {"url": url, "dest": None, "status": "failure",
                "message": f"下载 {url} 时出错: {e}"}

def download_images_from_csv(csv_file, url_column, dest_dir, max_workers, verbose=False, check_mode='pre'):
    """
    从 CSV 文件中读取指定列的 URL，
    根据参数 check_mode 来决定检查方式：
      - check_mode='pre': 使用多线程并行预检查文件是否已存在，在提交任务前过滤已下载的文件；
      - check_mode='during': 跳过预检查，下载时在 download_image 内检查文件是否存在。
    然后采用多进程并行下载剩余图片，并通过 tqdm 进度条实时显示总下载数、成功数与失败数。
    所有循环均使用 tqdm 监控进度，并打印大步骤的 log 信息。
    """
    # 步骤1：检查并创建目标目录
    print("步骤1：检查并创建目标目录...")
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        print(f"创建目标目录：{dest_dir}")
    else:
        print(f"目标目录已存在：{dest_dir}")

    # 步骤2：读取 CSV 文件
    print(f"步骤2：开始读取 CSV 文件：{csv_file} ...")
    urls = []
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in tqdm(reader, desc="读取 CSV 行", unit="行"):
            if row[url_column]:
                urls.append(row[url_column])
    print(f"CSV 文件读取完成，共找到 {len(urls)} 个 URL。")

    # 步骤3：检查已存在数据（预检查模式）或跳过该步骤
    if check_mode == 'pre':
        print("步骤3：使用多线程并行检查已存在数据，过滤已完成下载的文件...")
        tasks = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            check_results = list(tqdm(executor.map(lambda u: check_task(u, dest_dir),
                                                     urls),
                                        total=len(urls), desc="检查存在状态", unit="文件"))
        for url, skip, message in check_results:
            if skip:
                if verbose:
                    print(message)
            else:
                tasks.append(url)
        print(f"预检查完成，共计 {len(tasks)} 个文件需要下载。")
    else:
        print("步骤3：跳过预检查，在下载过程中检查文件是否存在...")
        tasks = urls

    # 步骤4：开始下载任务（多进程下载）
    print("步骤4：开始多进程下载任务...")
    results = []
    success_count = 0
    failure_count = 0
    # 判断是否在下载时检查文件是否存在
    check_during = (check_mode == 'during')
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_image, url, dest_dir, None, check_during): url for url in tasks}
        with tqdm(total=len(futures), desc="下载进度", unit="任务") as pbar:
            for future in as_completed(futures):
                result = future.result()
                if result["status"] == "success":
                    success_count += 1
                    if verbose:
                        print(result["message"])
                elif result["status"] == "skipped":
                    # 对于跳过的文件，不计入成功或失败，可以单独统计
                    if verbose:
                        print(result["message"])
                else:
                    failure_count += 1
                    print(result["message"])
                pbar.set_postfix({"成功": success_count, "失败": failure_count})
                pbar.update(1)
                results.append(result)
    print("步骤5：下载任务全部结束。")
    return results

def main():
    print("程序开始运行...")
    parser = argparse.ArgumentParser(description="根据 CSV 文件指定列的 URL 下载图片")
    parser.add_argument('--csv_file', type=str, required=True, help="CSV 文件路径")
    parser.add_argument('--url_column', type=str, required=True, help="CSV 文件中包含 URL 的列名称")
    parser.add_argument('--dest_dir', type=str, default='downloaded_images',
                        help="图片保存的目标目录，默认为 downloaded_images")
    parser.add_argument('--max_workers', type=int, default=os.cpu_count(),
                        help="并发（多进程/多线程）数，默认值为 CPU 核心数")
    parser.add_argument('--verbose', action='store_true', help="开启详细模式，仅打印成功下载的信息")
    parser.add_argument('--check_mode', type=str, choices=['pre', 'during'], default='pre',
                        help="检查文件存在的时机：'pre'表示在任务启动前过滤已存在数据；'during'表示在下载过程中判断是否存在")
    
    args = parser.parse_args()
    
    download_images_from_csv(args.csv_file, args.url_column, args.dest_dir,
                             args.max_workers, args.verbose, args.check_mode)
    print("程序运行结束。")

if __name__ == '__main__':
    main()
