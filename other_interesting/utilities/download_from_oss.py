import os
import argparse
import oss2
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from tqdm import tqdm

def get_local_path(object_key, local_download_path):
    """构造本地文件完整路径，并确保父目录存在。"""
    local_file_path = os.path.join(local_download_path, object_key)
    local_dir = os.path.dirname(local_file_path)
    if not os.path.exists(local_dir):
        os.makedirs(local_dir, exist_ok=True)
    return local_file_path

def check_task(object_key, local_download_path):
    """
    预检查本地文件是否已存在且非空。
    返回 (object_key, skip_flag, message)：
      skip_flag=True 表示已存在，应跳过；
      message 用于 verbose 模式下输出。
    """
    local_file_path = os.path.join(local_download_path, object_key)
    if os.path.exists(local_file_path) and os.path.getsize(local_file_path) > 0:
        return (object_key, True, f"跳过已存在的文件：{local_file_path}")
    return (object_key, False, "")

def download_file(object_key, local_download_path,
                  access_key_id, access_key_secret, endpoint, bucket_name,
                  check_during=False):
    """
    下载单个 OSS 对象到本地。
    如果 check_during=True，则先检查本地文件存在性，再决定是否跳过。
    返回 dict 包含 status ("success","failure","skipped") 和 message。
    """
    local_file_path = get_local_path(object_key, local_download_path)
    if check_during:
        if os.path.exists(local_file_path) and os.path.getsize(local_file_path) > 0:
            return {"key": object_key, "status": "skipped",
                    "message": f"跳过已存在的文件：{local_file_path}"}
    try:
        auth = oss2.Auth(access_key_id, access_key_secret)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)
        bucket.get_object_to_file(object_key, local_file_path)
        return {"key": object_key, "status": "success",
                "message": f"已下载：{object_key} -> {local_file_path}"}
    except Exception as e:
        return {"key": object_key, "status": "failure",
                "message": f"下载 {object_key} 时出错: {e}"}

def download_from_oss(args):
    # 步骤1：检查/创建本地下载根目录
    print("步骤1：检查并创建本地下载目录...")
    if not os.path.exists(args.local_download_path):
        os.makedirs(args.local_download_path, exist_ok=True)
        print(f"创建本地下载目录：{args.local_download_path}")
    else:
        print(f"本地下载目录已存在：{args.local_download_path}")

    # 初始化 OSS bucket（仅用于列举）
    auth = oss2.Auth(args.access_key_id, args.access_key_secret)
    bucket = oss2.Bucket(auth, args.endpoint, args.bucket_name)

    # 步骤2：列举 OSS 对象
    print(f"步骤2：列举 OSS 中前缀为 '{args.oss_folder_path}' 的对象...")
    object_keys = []
    for obj in tqdm(oss2.ObjectIterator(bucket, prefix=args.oss_folder_path),
                    desc="列举 OSS 文件", unit="对象"):
        object_keys.append(obj.key)
    print(f"共找到 {len(object_keys)} 个对象。")

    # 步骤3：预检查或跳过预检查
    if args.check_mode == 'pre':
        print("步骤3：使用多线程并行预检查本地文件存在状态...")
        tasks = []
        skip_count = 0
        to_dl_count = 0
        with ThreadPoolExecutor(max_workers=args.processes) as executor:
            futures = {executor.submit(check_task, key, args.local_download_path): key
                       for key in object_keys}
            with tqdm(total=len(object_keys),
                      desc="检查存在状态", unit="个",
                      ) as pbar:
                for future in as_completed(futures):
                    key, skip, msg = future.result()
                    if skip:
                        skip_count += 1
                        if args.verbose:
                            print(msg)
                    else:
                        to_dl_count += 1
                        tasks.append(key)
                    pbar.set_postfix({"跳过": skip_count, "待下载": to_dl_count})
                    pbar.update(1)
        print(f"预检查完成：{to_dl_count} 个待下载，{skip_count} 个已跳过。")
    else:
        print("步骤3：跳过预检查，下载过程中再检查是否已存在...")
        tasks = object_keys

    # 步骤4：多进程并行下载
    print("步骤4：开始并行下载任务...")
    success_count = 0
    failure_count = 0
    skipped_count = 0
    results = []
    with ProcessPoolExecutor(max_workers=args.processes) as executor:
        futures = {
            executor.submit(
                download_file,
                key,
                args.local_download_path,
                args.access_key_id,
                args.access_key_secret,
                args.endpoint,
                args.bucket_name,
                args.check_mode == 'during'
            ): key
            for key in tasks
        }
        with tqdm(total=len(futures), desc="下载进度", unit="个") as pbar:
            for future in as_completed(futures):
                res = future.result()
                status = res["status"]
                if status == "success":
                    success_count += 1
                    if args.verbose:
                        print(res["message"])
                elif status == "skipped":
                    skipped_count += 1
                    if args.verbose:
                        print(res["message"])
                else:
                    failure_count += 1
                    print(res["message"])
                pbar.set_postfix({
                    "成功": success_count,
                    "失败": failure_count,
                    "跳过": skipped_count
                })
                pbar.update(1)
                results.append(res)

    print("步骤5：下载任务完成。")
    print(f"结果统计 -> 成功: {success_count}, 失败: {failure_count}, 跳过: {skipped_count}")

def main():
    print("程序开始运行...")
    parser = argparse.ArgumentParser(description="并行从 OSS 下载文件，支持预检查和下载时检查")
    parser.add_argument('--access_key_id',     required=True, help='OSS Access Key ID')
    parser.add_argument('--access_key_secret', required=True, help='OSS Access Key Secret')
    parser.add_argument('--endpoint',          default='oss-cn-hangzhou.aliyuncs.com', help='OSS endpoint')
    parser.add_argument('--bucket_name',       required=True, help='OSS Bucket 名称')
    parser.add_argument('--oss_folder_path',   default='', help='OSS 前缀路径 (e.g. "myfolder/")')
    parser.add_argument('--local_download_path', default='./downloads/', help='本地保存目录')
    parser.add_argument('--processes',         type=int, default=4, help='并行线程/进程数')
    parser.add_argument('--verbose',           action='store_true', help='开启详细日志模式')
    parser.add_argument('--check_mode',        choices=['pre','during'], default='pre',
                                         help="检查时机：'pre' 启动前预检查；'during' 下载时检查")

    args = parser.parse_args()
    download_from_oss(args)
    print("程序运行结束。")

if __name__ == '__main__':
    main()
