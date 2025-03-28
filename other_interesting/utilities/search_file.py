import os
import multiprocessing
import argparse
from tqdm import tqdm

def process_directory(args):
    """
    扫描单个目录，返回匹配的文件列表和子目录列表
    :param args: (目录路径, 关键字)
    :return: (匹配的文件列表, 子目录列表)
    """
    directory, keyword = args
    matched = []
    subdirectories = []
    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_file():
                    if keyword in entry.name.lower():
                        matched.append(entry.path)
                elif entry.is_dir(follow_symlinks=False):
                    subdirectories.append(entry.path)
    except Exception as e:
        # 遇到权限等问题时忽略
        pass
    return matched, subdirectories

def main():
    parser = argparse.ArgumentParser(description="并行递归文件搜索工具")
    parser.add_argument("--root_dir", "-r", help="搜索根目录")
    parser.add_argument("--keyword", "-k", help="模糊匹配文件名关键字")
    args = parser.parse_args()

    # 如果命令行参数提供，则使用，否则交互式输入
    if args.root_dir:
        root_dir = args.root_dir.strip()
    else:
        root_dir = input("请输入搜索根目录：").strip()

    if not os.path.isdir(root_dir):
        print("目录不存在或无效！")
        return

    if args.keyword:
        keyword_input = args.keyword.strip()
    else:
        keyword_input = input("请输入要模糊搜索的文件名关键字：").strip()
        
    if not keyword_input:
        print("关键字不能为空！")
        return
    keyword = keyword_input.lower()

    # 初始化目录列表，起始目录为用户指定的根目录
    directories = [root_dir]
    all_matched = []
    
    # 创建多进程池，使用CPU核心数
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    
    # 使用 tqdm 显示扫描进度
    pbar = tqdm(total=len(directories), desc="扫描目录中")
    
    while directories:
        tasks = [(d, keyword) for d in directories]
        results = pool.map(process_directory, tasks)
        pbar.update(len(directories))
        new_directories = []
        for matched, subdirs in results:
            all_matched.extend(matched)
            new_directories.extend(subdirs)
        directories = new_directories
        pbar.total += len(new_directories)
    
    pbar.close()
    pool.close()
    pool.join()
    
    if all_matched:
        print("\n找到以下匹配的文件:")
        for file in all_matched:
            print(file)
    else:
        print("\n未找到符合条件的文件。")

if __name__ == '__main__':
    main()
