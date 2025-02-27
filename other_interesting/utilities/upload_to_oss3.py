import os
import oss2
import argparse
from multiprocessing import Pool, Manager
from tqdm import tqdm
import time

# 配置OSS账号信息
class OSSConfig:
    def __init__(self, access_key_id, access_key_secret, endpoint, bucket_name):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.endpoint = endpoint
        self.bucket_name = bucket_name

# 上传单个文件到OSS，增加文件存在检查并增加重试机制
def upload_file(config, local_file, oss_file):
    retries = 10  # 最大重试次数
    for attempt in range(retries):
        try:
            # 初始化OSS客户端
            auth = oss2.Auth(config.access_key_id, config.access_key_secret)
            bucket = oss2.Bucket(auth, config.endpoint, config.bucket_name)

            # 检查目标文件是否已存在
            if bucket.object_exists(oss_file):
                print(f"File {oss_file} already exists, skipping upload.")
                return True  # 跳过上传，标记为成功
            else:
                # 上传文件
                print(f"Uploading {local_file} to {oss_file}")
                bucket.put_object_from_file(oss_file, local_file)

                # 成功上传后返回成功标志
                return True
        except oss2.exceptions.OssError as e:
            # 捕获并打印上传错误信息
            print(f"Error uploading {local_file} to {oss_file}: {e}")
            if attempt < retries - 1:
                print(f"Retrying {local_file} to {oss_file}... Attempt {attempt + 2}/{retries}")
                # time.sleep(5)  # 等待 5 秒后再重试
            else:
                print(f"Failed to upload {local_file} after {retries} attempts.")
                return False

# 用于将文件上传的函数（用于 multiprocessing）
def process_file_for_upload(file_info):
    config, local_file, oss_file = file_info
    return upload_file(config, local_file, oss_file)

# 上传目录中的所有文件到OSS
def upload_directory(config, local_dir, oss_dir):
    # 获取目录下所有文件
    files = []
    for root, _, filenames in os.walk(local_dir):
        for filename in filenames:
            local_file = os.path.join(root, filename)
            # 计算文件在OSS中的路径
            oss_file = os.path.join(oss_dir, os.path.relpath(local_file, local_dir))
            files.append((config, local_file, oss_file))
    
    # 显示进度条
    with tqdm(total=len(files), unit="file", desc="Uploading Files") as pbar:
        # 创建进程池并并行上传
        with Pool() as pool:
            # 使用 imap_unordered 来并行处理任务并更新进度条
            results = pool.imap_unordered(process_file_for_upload, files)

            # 更新进度条
            for result in results:
                if result:  # 如果上传成功
                    pbar.update(1)

# 主函数：解析命令行参数并启动上传
def main():
    # 示例命令
    # python utilities/upload_to_oss.py --local_dir ./dense_caption/ --oss_dir ai_images/xd2/Downloads/images/
    
    # 命令行参数配置
    parser = argparse.ArgumentParser(description="Upload a folder to OSS")
    parser.add_argument('--access_key_id', required=True, help="Your OSS Access Key ID")
    parser.add_argument('--access_key_secret', required=True, help="Your OSS Access Key Secret")
    parser.add_argument('--endpoint', default='oss-cn-hangzhou.aliyuncs.com', help="OSS endpoint (e.g., oss-cn-hangzhou.aliyuncs.com)")
    parser.add_argument('--bucket_name', default='oss-datawork', help="Your OSS Bucket name")
    parser.add_argument('--local_dir', required=True, help="The local directory to upload")
    parser.add_argument('--oss_dir', required=True, help="The destination directory in OSS")
    
    # 解析命令行参数
    args = parser.parse_args()

    # 配置OSS
    config = OSSConfig(
        access_key_id=args.access_key_id,
        access_key_secret=args.access_key_secret,
        endpoint=args.endpoint,
        bucket_name=args.bucket_name
    )

    # 上传文件夹
    upload_directory(config, args.local_dir, args.oss_dir)

if __name__ == '__main__':
    main()
