import os
import requests
import json
import base64
import urllib.parse
import urllib.request
import logging
import random
import yaml

# 设置日志
logging.basicConfig(level=logging.INFO)

def openai_url():
    port = random.randint(*API_CONFIG["openai"]["port_range"])
    url = f"{API_CONFIG['openai']['url']}:{port}/proxy-openai"
    return url

def load_config(config_path=None):
    """加载配置文件"""
    if config_path is None:
        config_path = os.getenv('CONFIG_PATH', '/data1/A800-01/data/xinzhedeng/MyCode/Project/labelstudio/config/config.yaml')    
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logging.error(f"加载配置文件失败: {e}")
        raise

API_CONFIG = load_config()

def encode_image(image_path: str) -> str:
    """将图像编码为base64字符串。"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logging.error(f"图像编码失败: {e}")
        raise

def call_image_caption(image_path: str, in_prompt: str, model: str = "gpt-4o-mini", temperature: float = 0.7) -> dict:
    """调用图像描述API。"""
    system_prompt = "你是一个服装设计大师、服装工艺大师、面料专家、摄影构图专家,时尚杂志排版专家。请按照我的要求描述我提供的电商模特图。"
    
    if not isinstance(in_prompt, str):
        raise ValueError("in_prompt必须是字符串类型")
    
    if image_path.startswith('http'):
        image = image_path
    elif os.path.splitext(image_path)[1].lower() in ['.jpg', '.png', '.jpeg', '.bmp']:
        datas = encode_image(image_path)
        image = f"data:image/jpeg;base64,{datas}"
    else:
        raise ValueError("不支持的图像格式")
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [{"type": "text", "text": in_prompt}, {"type": "image_url", "image_url": {"url": image}}]}
        ],
        "temperature": temperature
    }
    
    url = openai_url() 
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"请求发生错误: {e} - URL: {url} - 数据: {data}")
        return None

def call_merge(in_prompt: str, model: str = "gpt-4o-mini", temperature: float = 0.7) -> dict:
    """调用内容融合API。"""
    system_prompt = "你是一个语言学家、逻辑学家、服装设计大师、服装工艺大师、面料专家、摄影构图专家,时尚杂志排版专家。请按照我的要求对提供的内容进行富有逻辑的提取、融合。"
    
    if not isinstance(in_prompt, str):
        raise ValueError("in_prompt必须是字符串类型")
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [{"type": "text", "text": in_prompt}]}
        ],
        "temperature": temperature
    }
    
    url = openai_url()
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"请求发生错误: {e} - URL: {url} - 数据: {data}")
        return None

def trans_xn(sentence: str, src_lan: str = 'en', tgt_lan: str = 'zh', apikey: str = None) -> str:
    """调用小牛翻译API进行翻译。"""
    if apikey is None:
        apikey = API_CONFIG["niutrans"]["api_key"]
    
    if not apikey:
        raise ValueError("API Key未设置")
    
    url = 'http://api.niutrans.com/NiuTransServer/translation?'
    data = {"from": src_lan, "to": tgt_lan, "apikey": apikey, "src_text": sentence}
    data_en = urllib.parse.urlencode(data)
    req = url + "&" + data_en
    
    try:
        res = urllib.request.urlopen(req).read()
        res_dict = json.loads(res)
        return res_dict.get('tgt_text', res)
    except Exception as e:
        logging.error(f"翻译请求发生错误: {e}")
        return None

def trans_gpt(in_prompt: str, model: str = "gpt-4o-mini", temperature: float = 0.7) -> dict:
    """调用内容融合API。"""
    system_prompt = "你是一个中英语翻译大师。无论我给你哪种语言你都可以准确的帮我翻译成另一种语言。比如，我给你中文，你可以很准确的翻译成英文。我给你英文，同理，你可以很准确翻译成中文。"
    
    if not isinstance(in_prompt, str):
        raise ValueError("in_prompt必须是字符串类型")
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [{"type": "text", "text": in_prompt}]}
        ],
        "temperature": temperature
    }
    
    url = openai_url() 
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"请求发生错误: {e} - URL: {url} - 数据: {data}")
        return None
    
def gpt(url: str, all_others: dict, base_prompt: str, merge_prompt: str) -> dict:
    """生成图像描述和合并内容的函数。"""
    # 初始化结果字典
    rst_dict = {
        'image_caption_en': None,
        'image_caption_cn': None,
        'all_others_en': None,
        'all_others_cn': None,
        'merged_caption_en': None,
        'merged_caption_cn': None
    }

    # 尝试生成图像描述
    image_caption_en = call_image_caption(url, in_prompt=base_prompt)
    if image_caption_en:
        rst_dict['image_caption_en'] = image_caption_en
        try:
            rst_dict['image_caption_cn'] = trans_gpt(image_caption_en).replace('\n\n', '<br><br>')
        except Exception:
            rst_dict['image_caption_cn'] = trans_gpt(image_caption_en)
            
    # 翻译 all_others 并更新字典
    all_others_en = json.dumps(all_others)
    if all_others_en:
        rst_dict['all_others_en'] = all_others_en
        try:
            rst_dict['all_others_cn'] = trans_gpt(all_others_en)
        except Exception:
            rst_dict['all_others_cn'] = all_others_en

    # 尝试生成合并描述
    if image_caption_en and all_others_en:
        case_merge_prompt = merge_prompt.replace('ZJ_BASE_CAP', image_caption_en).replace('ZJ_ALL_OTH', all_others_en)
        merged_caption_en = call_merge(case_merge_prompt)
        if merged_caption_en:
            rst_dict['merged_caption_en'] = merged_caption_en
            try:
                rst_dict['merged_caption_cn'] = trans_gpt(merged_caption_en).replace('\n\n', '<br><br>')
            except Exception:
                rst_dict['merged_caption_cn'] = trans_gpt(merged_caption_en)

    return rst_dict
    
# 主程序示例
if __name__ == '__main__':
    
    image_caption = call_image_caption("https://oss-proxy.textile-story.com/images_en/v1/meida_1/19ba1be71f913215b9e2dcb9886f697d_1708753009579_2723df3310f84db8b5abac8eaa7cd862.jpg", "描述这个图像")
    merged_content = call_merge("合并的内容")
    translated_text = trans_xn("Hello, world!", apikey=API_CONFIG["niutrans"]["api_key"])
    
    print(f"image_caption: {image_caption}\n")
    print(f"merged_content: {merged_content}\n")
    print(f"translated_text: {translated_text}\n")
    
    # 使用 gpt 函数示例
    url = "https://oss-proxy.textile-story.com/images_en/v1/meida_1/19ba1be71f913215b9e2dcb9886f697d_1708753009579_2723df3310f84db8b5abac8eaa7cd862.jpg"
    all_others = {"color": "red", "style": "casual"}
    base_prompt = "描述这个图像的风格和特点。"
    merge_prompt = "请将ZJ_BASE_CAP和ZJ_ALL_OTH进行融合。"

    from parser import get_base_prompt, get_merge_prompt
    
    config_path = "/data1/A800-01/data/xinzhedeng/MyCode/Project/labelstudio/config/prompts.py"
    base_prompt = get_base_prompt(config_path)
    merge_prompt = get_merge_prompt(config_path)

    gpt_result = gpt(url, all_others, base_prompt, merge_prompt)
    print(f"gpt_result: {gpt_result}\n")
