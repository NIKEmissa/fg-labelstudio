import os
import oss2
import argparse
from multiprocessing import Pool

# 下载单个文件
def download_file(bucket, object_name, local_download_path):
    # 目标本地文件路径
    local_file_path = os.path.join(local_download_path, object_name)

    # 确保本地目录存在
    local_dir = os.path.dirname(local_file_path)
    if not os.path.exists(local_dir):
        os.makedirs(local_dir, exist_ok=True)  # 修改这里，允许目录已存在

    try:
        # 下载文件
        bucket.get_object_to_file(object_name, local_file_path)
        print(f"Downloaded {object_name} to {local_file_path}")
    except Exception as e:
        print(f"Failed to download {object_name}: {str(e)}")

# 获取OSS中指定路径下的文件
def list_files(bucket, oss_folder_path):
    files = []
    for object_info in oss2.ObjectIterator(bucket, prefix=oss_folder_path):
        files.append(object_info.key)
    return files

# 多进程下载文件
def download_files_concurrently(bucket, oss_folder_path, local_download_path, processes):
    # 获取指定路径下的文件列表
    files = list_files(bucket, oss_folder_path)

    # 使用多进程池下载文件
    with Pool(processes=processes) as pool:
        pool.starmap(download_file, [(bucket, file, local_download_path) for file in files])

def main(args):
    # 初始化OSS认证
    auth = oss2.Auth(args.access_key_id, args.access_key_secret)
    bucket = oss2.Bucket(auth, args.endpoint, args.bucket_name)

    # 创建本地下载目录
    if not os.path.exists(args.local_download_path):
        os.makedirs(args.local_download_path, exist_ok=True)  # 修改这里，允许目录已存在
        print(f"Created local download directory: {args.local_download_path}")

    # 开始多进程下载
    download_files_concurrently(bucket, args.oss_folder_path, args.local_download_path, args.processes)

if __name__ == '__main__':
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='Download files from OSS with multi-process.')
    parser.add_argument('--access_key_id', required=True, help='Your OSS Access Key ID')
    parser.add_argument('--access_key_secret', required=True, help='Your OSS Access Key Secret')
    parser.add_argument('--endpoint', default='oss-cn-hangzhou.aliyuncs.com', help="OSS endpoint (e.g., oss-cn-hangzhou.aliyuncs.com)")
    parser.add_argument('--bucket_name', default='zj-aigc-data', help="Your OSS Bucket name")
    parser.add_argument('--local_download_path', default='./downloads/', help='Local directory to save the downloaded files')
    parser.add_argument('--oss_folder_path', default='', help='The OSS folder path to download files from (e.g., "myfolder/")')
    parser.add_argument('--processes', type=int, default=4, help='Number of processes for parallel downloading')

    # 解析命令行参数
    args = parser.parse_args()

    # 执行主函数
    main(args)
