import os
import csv
import requests
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
from urllib.parse import urlparse
from tqdm import tqdm
from PIL import Image  # 新增用于验证图片

# 可选解密依赖
import zjimagetool
# 默认解密令牌，可通过 --decrypt-token 覆盖
DEFAULT_DECRYPT_TOKEN = "4n=O<kx!47z}Mv}*"


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
    返回三元组 (url, skip_flag, message)。
    """
    filename = get_filename(url)
    dest_path = os.path.join(dest_dir, filename)
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return (url, True, f"跳过已存在的文件：{dest_path}")
    else:
        return (url, False, "")


def download_image(url, dest_dir, filename=None, check_during=False, decrypt=False):
    """
    下载或解密下载图片。若 decrypt=True，则尝试对响应内容解密。
    若 check_during 为 True，则在下载前检查文件是否已存在，若存在则跳过。
    返回包含状态和信息的字典。
    """
    # 检查是否跳过
    if check_during:
        if not filename:
            filename = get_filename(url)
        dest_path = os.path.join(dest_dir, filename)
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
            return {"url": url, "dest": dest_path, "status": "skipped",
                    "message": f"跳过已存在的文件：{dest_path}"}
    try:
        response = requests.get(url, stream=not decrypt, timeout=10)
        response.raise_for_status()
        if not filename:
            filename = get_filename(url)
        dest_path = os.path.join(dest_dir, filename)

        # 解密模式
        if decrypt:
            try:
                raw_data = response.content
                decrypted = zjimagetool.decrypt(raw_data)
                with open(dest_path, 'wb') as f:
                    f.write(decrypted)
            except Exception:
                # 解密失败时回退至直接写入原始数据
                with open(dest_path, 'wb') as f:
                    f.write(response.content)
        else:
            # 普通模式：分块写入
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)

        return {"url": url, "dest": dest_path, "status": "success",
                "message": f"已下载：{url} -> {dest_path}"}
    except Exception as e:
        return {"url": url, "dest": None, "status": "failure",
                "message": f"下载 {url} 时出错: {e}"}


def is_image_valid(path):
    """
    使用 PIL 验证图片文件有效性。
    """
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def download_images_from_csv(csv_file, url_column, dest_dir,
                             max_workers, verbose=False,
                             check_mode='pre', decrypt=False):
    """
    从 CSV 文件读取 URL 并并行下载，下载完成后即时验证图片有效性。
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
            if row.get(url_column):
                urls.append(row[url_column])
    print(f"CSV 文件读取完成，共找到 {len(urls)} 个 URL。")

    # 步骤3：预检查或跳过
    if check_mode == 'pre':
        print("步骤3：使用多线程并行检查已存在数据，过滤已完成下载的文件...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            check_results = list(tqdm(
                executor.map(lambda u: check_task(u, dest_dir), urls),
                total=len(urls), desc="检查存在状态", unit="文件"
            ))
        tasks = []
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

    # 步骤4：多进程下载 + 验证有效性
    print("步骤4：开始多进程下载并验证任务...")
    results = []
    success_count = 0
    download_fail_count = 0
    validate_fail_count = 0
    check_during = (check_mode == 'during')

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(download_image, url, dest_dir, None, check_during, decrypt): url
            for url in tasks
        }
        with tqdm(total=len(futures), desc="下载 & 验证", unit="任务") as pbar:
            for future in as_completed(futures):
                res = future.result()
                # 仅对“success”状态进行图片有效性验证
                if res["status"] == "success" and res["dest"]:
                    if is_image_valid(res["dest"]):
                        success_count += 1
                        if verbose:
                            print(f"验证通过：{res['dest']}")
                    else:
                        # 验证失败，删除文件
                        try:
                            os.remove(res["dest"])
                        except:
                            pass
                        res["status"] = "failure"
                        res["message"] += "；验证失败，已删除无效文件"
                        validate_fail_count += 1
                        if verbose:
                            print(res["message"])
                elif res["status"] == "skipped":
                    # 跳过的当作成功
                    success_count += 1
                    if verbose:
                        print(res["message"])
                else:
                    # download 或其他失败
                    download_fail_count += 1
                    if verbose:
                        print(res["message"])

                results.append(res)
                pbar.set_postfix({
                    "成功": success_count,
                    "下载失败": download_fail_count,
                    "解析失败": validate_fail_count
                })
                pbar.update(1)

    print("步骤5：所有任务完成。")
    print(f"结果：{success_count} 成功, {failure_count} 失败, 总计 {len(tasks)}")
    return results


def main():
    parser = argparse.ArgumentParser(
        description="根据 CSV 文件指定列的 URL 下载并验证图片（支持解密模式）"
    )
    parser.add_argument('--csv_file', type=str, required=True, help="CSV 文件路径")
    parser.add_argument('--url_column', type=str, required=True, help="CSV 文件中包含 URL 的列名称")
    parser.add_argument('--dest_dir', type=str, default='downloaded_images',
                        help="图片保存的目标目录")
    parser.add_argument('--max_workers', type=int, default=os.cpu_count(),
                        help="并发线程/进程数，默认 CPU 核心数")
    parser.add_argument('--verbose', action='store_true', help="开启详细模式")
    parser.add_argument('--check_mode', choices=['pre', 'during'], default='pre',
                        help="检查模式：'pre' 或 'during'")
    parser.add_argument('--decrypt', action='store_true', help="启用解密下载模式")
    parser.add_argument('--decrypt-token', type=str, default=None,
                        help="指定解密令牌，默认使用脚本内置令牌")
    args = parser.parse_args()

    # 设置解密令牌
    if args.decrypt:
        token = args.decrypt_token or DEFAULT_DECRYPT_TOKEN
        os.environ['IMG_ENCRYPT_TOKEN'] = token

    download_images_from_csv(
        args.csv_file,
        args.url_column,
        args.dest_dir,
        args.max_workers,
        args.verbose,
        args.check_mode,
        args.decrypt
    )


if __name__ == '__main__':
    main()
