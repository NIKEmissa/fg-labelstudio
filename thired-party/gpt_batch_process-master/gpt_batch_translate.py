import os
import requests
import json
import base64
import threading
import queue
import time
import logging
import argparse
from tqdm import tqdm


# 日志配置
logging.basicConfig(
    filename='log/data_translation.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 默认参数
MAX_RETRY_COUNT = 3
BATCH_SIZE_PRINT = 100

# 全局计数器和锁
count_lock = threading.Lock()


def encode_image(image_path):
    """ 将图片文件编码为 base64 字符串 """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logging.error(f"Image encoding error for {image_path}: {e}")
        return None

def call_proxy_openai(data, port):
    """ 调用中转服务，返回结果 """
    url = f"http://8.219.81.65:{port}/proxy-openai"
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Error {response.status_code}: {response.json()}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Request exception for port {port}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error for port {port}: {e}")
        return None

def save_result(result, output_dir, file_prefix="result"):
    """ 保存打标结果为单独文件 """
    try:
        file_name = os.path.join(output_dir, f"{file_prefix}_{result['id']}.json")
        with open(file_name, "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        logging.info(f"Result saved: {file_name}")
        update_progress(1)
    except Exception as e:
        logging.error(f"Failed to save result for id {result['id']}: {e}")

def process_data(data, model, port, output_dir, retry_count=0):
    """ 处理单个数据项的打标逻辑 """
    try:
        file_prefix = "result"
        result_file = os.path.join(output_dir, f"{file_prefix}_{data['id']}.json")
        if os.path.isfile(result_file):
            return
        
        user_prompt = USER_PROMPT.replace("text", data["text"])
        request_data = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "text", "text": user_prompt},
                ]}
            ],
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
        }

        # 调用中转服务
        response = call_proxy_openai(request_data, port)
        if response:
            # 打标成功，保存结果
            result = {
                "id": data["id"],
                "goods_id": data["goods_id"],
                "url": data["url"],
                "category": data["category"],
                "gpt_translation": response
            }
            save_result(result, output_dir, file_prefix)
        else:
            # 打标失败，判断是否达到最大重试次数
            if retry_count < MAX_RETRY_COUNT:
                logging.warning(f"Failed to label data id: {data['id']}. Retrying (attempt {retry_count + 1}).")
                data_queue.put((data, retry_count + 1))
            else:
                logging.error(f"Failed to label data id: {data['id']} after {MAX_RETRY_COUNT} attempts. Marking as failed.")
                failed_data_list.append(data)
    except Exception as e:
        logging.error(f"Encountered an error with data id: {data['id']}: {e}")
        if retry_count < MAX_RETRY_COUNT:
            data_queue.put((data, retry_count + 1))
        else:
            failed_data_list.append(data)

def update_progress(count):
    """更新全局处理进度，并打印进度信息"""
    global processed_count
    with count_lock:
        processed_count += count
        if processed_count % BATCH_SIZE_PRINT == 0:
            elapsed_time = time.time() - start_time
            speed = (processed_count - skipped_labeled_data) / elapsed_time
            print(f"Processed {processed_count}/{data_count}, speed: {speed:.2f} items/sec")
            logging.info(f"Processed {processed_count}/{data_count}, speed: {speed:.2f} items/sec")


def worker_thread(port, model, output_dir):
    """ 线程工作函数，负责从队列中获取数据并处理 """
    while not data_queue.empty():
        try:
            data, retry_count = data_queue.get(timeout=1)
            process_data(data, model, port, output_dir, retry_count)
            data_queue.task_done()            
        except queue.Empty:
            logging.info(f"No more data to process for port {port}")
            break
            
def supervisor(ports, model, output_dir):
    """ 监督线程，处理打标失败的重试逻辑 """
    while not retry_queue.empty():
        try:
            data, retry_count = retry_queue.get(timeout=1)
            data_queue.put((data, retry_count))
        except queue.Empty:
            break

    if not data_queue.empty():
        start_workers(ports, model, output_dir)  # 重新启动 worker 线程处理

def start_workers(ports, model, output_dir):
    processes = []
    num_threads = len(ports)
    """ 启动 worker 线程 """
    for i in range(num_threads):
        port = ports[i % num_threads]
        thread = threading.Thread(target=worker_thread, args=(port, model, output_dir))
        thread.start()
        processes.append(thread)

    for p in processes:
        p.join()

def main(model, ports, label_file, output_dir, failed_dir):
    global data_queue, retry_queue, failed_data_list, start_time, data_count, processed_count, skipped_labeled_data

    # 读取数据
    data_list = []
    with open(label_file, mode='r', encoding='utf-8') as jsonl_file:
        for line in tqdm(jsonl_file, desc="Loading data"):
            json_obj = json.loads(line.strip())
            data_list.append(json_obj)
    data_count = len(data_list)
    logging.info(f"Total amount of data to be labeled: {data_count}")

    # 配置任务队列和其他共享资源
    data_queue = queue.Queue()
    retry_queue = queue.Queue()
    failed_data_list = []
    
    for item in tqdm(data_list, desc="Pushing data into queue"):
        data_queue.put((item, 0))  # (数据项, 重试次数)

    # 开始计时
    start_time = time.time()
    skipped_labeled_data = len([f for f in os.listdir(output_dir) if f.endswith('.json')])
    processed_count = skipped_labeled_data
    print(f"Found {skipped_labeled_data} existing annotation, will be skipped")

    # 启动 worker 线程
    print("Start translating data ...")
    start_workers(ports, model, output_dir)
    data_queue.join()

    # 启动监督线程处理第一次打标失败的数据
    logging.info(f"Retry failed label: {len(failed_data_list)}")
    for item in failed_data_list:
        retry_queue.put((item, 0))
    failed_data_list = []
    supervisor_thread = threading.Thread(target=supervisor, args=(ports, model, output_dir))
    supervisor_thread.start()
    supervisor_thread.join()

    # 输出完全失败的统计数据
    if failed_data_list:
        logging.error(f"Total failed data count: {len(failed_data_list)}")
        with open(f"{failed_dir}/failed_data.json", "w") as f:
            json.dump(failed_data_list, f, ensure_ascii=False, indent=4)
        logging.info("Failed data saved to 'failed_data.json'")
    else:
        logging.info("No data failed completely.")
    logging.info("Data labeling task completed.")
    print("Finish translating!")


if __name__ == "__main__":
    from prompt.translate_prompt import SYSTEM_PROMPT, USER_PROMPT, TEMPERATURE, MAX_TOKENS
    PORTS = range(30011, 30015)

    parser = argparse.ArgumentParser(description="Data labeling with GPT model")
    parser.add_argument("--model", type=str, default="gpt-4o-mini-2024-07-18", help="GPT model to use")
    parser.add_argument("--ports", type=int, nargs='+', default=PORTS, help="List of ports to use for proxy services")
    parser.add_argument("--label_file", type=str, required=True, help="Path to the JSON file with data")
    parser.add_argument("--output_dir", type=str, default="output/batch_transl")
    parser.add_argument("--failed_dir", type=str, default="output/fail_transl")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.failed_dir, exist_ok=True)
    main(args.model, args.ports, args.label_file, args.output_dir, args.failed_dir)
