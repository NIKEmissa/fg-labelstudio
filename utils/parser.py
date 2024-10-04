# util/parser.py

import importlib.util
import os

def import_config_module(config_path):
    """
    动态导入指定路径的config.py模块。
    
    :param config_path: config.py的绝对路径
    :return: 导入的模块对象
    """
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Config file not found at path: {config_path}")

    spec = importlib.util.spec_from_file_location("config_module", config_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    return config_module

def get_prompt(prompt_name, config_path):
    """
    根据prompt名称和config.py路径返回相应的prompt内容。
    如果prompt不存在，返回空字符串。
    
    :param prompt_name: prompt名称，例如 "base_prompt" 或 "merge_prompt"
    :param config_path: config.py的绝对路径
    :return: 对应的prompt内容，或空字符串
    """
    config_module = import_config_module(config_path)
    return config_module.PROMPTS.get(prompt_name, "")

def get_base_prompt(config_path):
    """
    返回基础的预设prompt。
    
    :param config_path: config.py的绝对路径
    :return: base_prompt内容
    """
    return get_prompt("base_prompt", config_path)

def get_merge_prompt(config_path):
    """
    返回合并后的预设prompt。
    
    :param config_path: config.py的绝对路径
    :return: merge_prompt内容
    """
    return get_prompt("merge_prompt", config_path)

# 添加__main__用于测试
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse and display prompts from config.py")
    parser.add_argument("--config_path", type=str, required=True, help="Absolute path to config.py")
    parser.add_argument("--prompt_name", type=str, choices=["base_prompt", "merge_prompt"], required=True, help="Name of the prompt to retrieve")

    args = parser.parse_args()

    prompt_content = get_prompt(args.prompt_name, args.config_path)
    if prompt_content:
        print(f"{args.prompt_name}:\n")
        print(prompt_content)
    else:
        print(f"No content found for prompt: {args.prompt_name}")
