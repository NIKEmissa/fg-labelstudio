import oss2
import multiprocessing
import os
from tqdm import tqdm
import logging
import argparse

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 获取本地目录中的所有文件和目录，支持单一文件上传
def extract_file_names_and_dirs_from_local(local_path):
    logging.info('正在从本地路径中提取文件名和目录。')
    local_files = []
    
    if os.path.isfile(local_path):  # 如果是单个文件
        local_files.append(os.path.basename(local_path))
    else:  # 如果是目录
        for root, dirs, files in os.walk(local_path):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, local_path)
                local_files.append(relative_path)
                
    logging.info(f'从本地路径中提取了{len(local_files)}个文件。')
    return local_files

# 判断文件是否已经上传且完整
def is_file_uploaded(bucket, oss_key, local_file):
    try:
        oss_file_info = bucket.head_object(oss_key)
        local_size = os.path.getsize(local_file)
        return local_size == oss_file_info.content_length  # 比较本地文件大小和OSS文件大小
    except oss2.exceptions.NoSuchKey:
        logging.info(f'OSS中不存在该文件: {oss_key}')
        return False
    except Exception as e:
        logging.error(f'检查文件上传状态时出错: {oss_key} - {e}')
        return False

# 上传文件函数，包含断点续传判断和verbose参数
def upload_file_to_oss(local_oss_file):
    local_file, oss_key, bucket, verbose = local_oss_file
    try:
        if is_file_uploaded(bucket, oss_key, local_file):
            if verbose:
                logging.info(f'文件已上传且完整，跳过上传: {oss_key}')
            return True

        logging.info(f'开始上传 {oss_key}')
        with open(local_file, 'rb') as f:
            bucket.put_object(oss_key, f)
        logging.info(f'上传完成 {oss_key}')
        return True
    except Exception as e:
        logging.error(f'上传错误 {oss_key}: {e}')
        return False

# 获取OSS路径中已经存在的文件
def get_uploaded_files(bucket, prefix):
    logging.info('获取OSS路径中已经存在的文件。')
    uploaded_files = set()
    for obj in oss2.ObjectIterator(bucket, prefix=prefix):
        uploaded_files.add(obj.key)
    logging.info(f'发现{len(uploaded_files)}个已经上传的文件。')
    return uploaded_files

# 多进程上传函数
def upload_files_to_oss(files, bucket, local_dir, max_workers, verbose):
    with tqdm(total=len(files), unit='file', desc='正在上传文件') as pbar:
        with multiprocessing.Pool(max_workers) as pool:
            for _ in pool.imap_unordered(upload_file_to_oss, files):
                pbar.update(1)
    logging.info('文件上传完成。')

# 主程序
if __name__ == "__main__":
    
    # 参考命令
    # python3 upload_to_oss.py --access_key_id xxx --access_key_secret xxx --local_dir /data1/datasets/lqp/data/denseData/ --oss_dir ai_images/xd2/Downloads/images/dense_annotations/test_anno_images/spider/ --processes 120
    # 配置命令行参数
    parser = argparse.ArgumentParser(description="Upload a folder to OSS")
    parser.add_argument('--access_key_id', required=True, help="Your OSS Access Key ID")
    parser.add_argument('--access_key_secret', required=True, help="Your OSS Access Key Secret")
    parser.add_argument('--endpoint', default='oss-cn-hangzhou.aliyuncs.com', help="OSS endpoint (e.g., oss-cn-hangzhou.aliyuncs.com)")
    parser.add_argument('--bucket_name', default='oss-datawork', help="Your OSS Bucket name")
    parser.add_argument('--local_dir', required=True, help="The local directory to upload")
    parser.add_argument('--oss_dir', required=True, help="The destination directory in OSS")
    parser.add_argument('--processes', type=int, default=-1, help="Number of parallel processes. Use -1 for automatic detection based on CPU cores.")
    parser.add_argument('--verbose', type=bool, default=False, help="If True, show skipped files")

    args = parser.parse_args()

    # 使用提供的OSS认证信息
    auth = oss2.Auth(args.access_key_id, args.access_key_secret)
    bucket = oss2.Bucket(auth, args.endpoint, args.bucket_name)

    # 解析本地目录中的文件
    local_files = extract_file_names_and_dirs_from_local(args.local_dir)

    # 获取OSS路径中已经上传的文件
    uploaded_files = get_uploaded_files(bucket, args.oss_dir)

    # 计算需要上传的文件
    files_to_upload = set(local_files) - {key[len(args.oss_dir):] for key in uploaded_files}
    logging.info(f'需要上传的文件总数: {len(files_to_upload)}')

    # 准备本地文件路径和OSS文件路径的元组列表
    local_oss_file_pairs = []
    if os.path.isfile(args.local_dir):
        file_name = os.path.basename(args.local_dir)
        oss_key = os.path.join(args.oss_dir, file_name)
        local_oss_file_pairs.append((args.local_dir, oss_key, bucket, args.verbose))
    else:
        local_oss_file_pairs = [
            (os.path.join(args.local_dir, file), os.path.join(args.oss_dir, file), bucket, args.verbose)
            for file in files_to_upload
        ]

    # 自动检测CPU核心数（如果没有提供进程数）
    if args.processes == -1:
        max_workers = multiprocessing.cpu_count()
    else:
        max_workers = args.processes

    input('请按回车确认')
    
    # 多进程上传文件
    upload_files_to_oss(local_oss_file_pairs, bucket, args.local_dir, max_workers, args.verbose)
