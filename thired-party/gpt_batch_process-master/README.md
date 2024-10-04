## 目录

- **[1. 环境安装](#1-环境安装)**

- **[2. 图像描述批量打标](#2-图像描述批量打标)**

  - **[2.1 数据准备](#21-数据准备csv或jsonl)**

  - **[2.2 批量打标](#22-批量打标)**

  - **[2.3 合并结果](#23-合并结果)**

- **[3. GPT描述与GT批量融合](#3-gpt描述与gt批量融合)**

  - **[3.1 数据准备](#31-数据准备csv或jsonl)**

  - **[3.2 批量融合](#32-批量融合)**

  - **[3.3 合并结果](#33-合并结果)**

- **[4. 批量翻译](#4-批量翻译)**

  - **[4.1 数据准备](#41-数据准备csv或jsonl)**

  - **[4.2 批量翻译](#42-批量翻译)**

  - **[4.3 合并结果](#43-合并结果)**



## 1. 环境安装

```bash
pip install -r requirements.txt
```



## 2. 图像描述批量打标

### 2.1 数据准备（csv或jsonl）

- 准备批量打标的`jsonl`文件，`jsonl`是一种每行包含一个独立的 `JSON `对象的文本文件格式，必须包含的`key`为："`id`"、"`goods_id`"、"`url`"。"`category`"不强制包含，如果没有默认为“None”。

  ```json
  {"id": 1, "category": "dress", "goods_id": 8528627, "url": "https://oss-datawork-cdn.tiangong.tech/xxx.jpg"}
  {"id": 2, "category": "dress", "goods_id": 15493424, "url": "https://oss-datawork-cdn.tiangong.tech/xxx.jpg"}
  {"id": 3, "category": "dress", "goods_id": 16755541, "url": "https://oss-datawork-cdn.tiangong.tech/xxx.jpg"}
  ```

- 如果你有`csv`文件，同时包含"`id`"、"`goods_id`"、"`url`"信息，可以执行如下指令转换为jsonl文件

  ```bash
  python tools/data_convert.py --csv_file label_file.csv --json_file label_file.jsonl --convert_label
  ```

  - `--csv_file`： 待转换的`csv`文件路径；
  - `--json_file`：转换后保存的`jsonl`文件路径；
  - `--convert_label`：转换模式，默认转换`csv`的"`id`"、"`goods_id`"、"`url`"信息为`jsonl`文件。

### 2.2 批量打标

- 编辑`prompt/desc_prompt.py`文件，设置`TEMPERATURE`、`MAX_TOKENS`、`USER_PROMPT`和`SYSTEM_PROMPT`等GPT相关参数；

  ```python
  TEMPERATURE = 0.6
  MAX_TOKENS = 4096
  
  SYSTEM_PROMPT = """
  你是一个有用的人工智能助手。
  """
  
  USER_PROMPT = """
  ## Background:
  You are a master of fashion design, craftsmanship, fabric expertise, and photographic composition. You excel at providing comprehensive design details by examining images to help users recreate the clothing design through a text-to-image model.
  ...
  """
  ```

- 编辑`gpt_batch_label.py`文件中的`PORTS`变量，设置中转服务默认端口号

  ```python
  if __name__ == "__main__":
      from prompt.desc_prompt import SYSTEM_PROMPT, USER_PROMPT, TEMPERATURE, MAX_TOKENS
      PORTS = range(30021, 30081)
      ...
  ```

- 执行如下指令，进行批量打标

  ```bash
  python gpt_batch_label.py --model gpt-4o-mini-2024-07-18 --label_file label_file.jsonl --output_dir output/batch_label --failed_dir output/fail_label
  ```

  - `--model`：GPT模型类型，默认采用`gpt-4o-mini-2024-07-18`；

  - `--label_file`：待打标文件；

  - `--output_dir`：批处理输出文件夹，用于保存每一次请求返回的结果，初次执行必须为**空文件夹**；

  - `--failed_dir`：打标失败的文件保存在该文件夹下。

    **注意：**
    
    - **如果批量打标过程突然中断，重新执行上述指令可继续打标，会跳过已经打标过的实例**
    - **批量打标日志保存在`log/data_description.log`**

### 2.3 合并结果

- 合并打标结果和原始信息

```
python tools/merge_result.py --label_file label_file.jsonl --result_dir output/batch_label --merge_file label_result.csv
```

- `--label_file`：待打标文件；
- `--result_dir`：打标结果的文件夹路径；
- `--merge_file`：合并文件路径。



## 3. GPT描述与GT批量融合

### 3.1 数据准备（csv或jsonl）

- 准备批量打标的`jsonl`文件，`jsonl`是一种每行包含一个独立的 `JSON `对象的文本文件格式，必须包含的`key`为："`id`"、"`goods_id`"、"`url`"、"`All_prompts`"、"`All_gt`"。"`category`"不强制包含，如果没有默认为“None”。

  ```json
  {"id": 1, "category": "dress", "goods_id": 8528627, "url": "https://oss-datawork-cdn.tiangong.tech/xxx.jpg", "All_prompts": "The image showcases a xxx.", "All_gt": "{\"Category\": \"dress\", ..., \"Waist high\": \"High-waisted\"}"}
  {"id": 2, "category": "dress", "goods_id": 15493424, "url": "https://oss-datawork-cdn.tiangong.tech/xxx.jpg", "All_prompts": "The image features an xxx.", "All_gt": "{\"Category\": \"dress\", .., \"Front closure style\": \"No Front Opening\"}"}
  {"id": 3, "category": "dress", "goods_id": 16755541, "url": "https://oss-datawork-cdn.tiangong.tech/xxx.jpg", "All_prompts": "The image showcases an xxx.", "All_gt": "{\"Category\": \"blouse\", ..., \"Front closure style\": \"No Front Opening\"}"}
  ```

  - `All_prompts`：GPT打标的baseline描述。
  - `All_gt`：人工标注的结果，json格式。

- 如果你有`csv`文件，同时包含"`id`"、"`goods_id`"、"`url`"、"`All_prompts`"、"`All_gt`"信息，可以执行如下指令转换为jsonl文件

  ```bash
  python tools/data_convert.py --csv_file baseline_gt_file.csv --json_file baseline_gt_file.jsonl --convert_merge
  ```

  - `--csv_file`： 待转换的`csv`文件路径；
  - `--json_file`：转换后保存的`jsonl`文件路径；
  - `--convert_merge`：转换模式，默认转换`csv`文件的"`id`"、"`goods_id`"、"`url`"、"`All_prompts`"、"`All_gt`"信息为`jsonl`文件。

### 3.2 批量融合

- 编辑`prompt/merge_prompt.py`文件，设置`TEMPERATURE`、`MAX_TOKENS`、`USER_PROMPT`和`SYSTEM_PROMPT`等GPT相关参数；

  ```python
  TEMPERATURE = 0.6
  MAX_TOKENS = 4096
  
  SYSTEM_PROMPT = """
  你是一个有用的人工智能助手。
  """
  
  ALL_GPT_PROMPT_KEYWORD = "ZJ_BASE_CAP"
  ALL_GT_KEYWORD = "ZJ_ALL_OTH"
  USER_PROMPT = f"""
  ## Background:
  我会在下面的[Context]中提供[服装描述A],[款式真值B]，根据我的要求，需要从[服装描述A]、[款式真值B]中有机的提取相应的设计要素最终组合成一段简洁明了、具备逻辑性的服装文生图提示词。
  ## Context:
  ### 服装描述A:{ALL_GPT_PROMPT_KEYWORD}
  ### 款式真值B:{ALL_GT_KEYWORD}
  ## Definition:
  ### Design Elements
  1. **Garment Categories** - Tops, Bottoms, Dresses, Suits and Sets, Outerwear, Others, Accessories, etc.  
  ...
  """
  ```

- 编辑`gpt_batch_merge.py`文件中的`PORTS`变量，设置中转服务默认端口号

  ```python
  if __name__ == "__main__":
      from prompt.merge_prompt import SYSTEM_PROMPT, USER_PROMPT, TEMPERATURE, MAX_TOKENS, ALL_GPT_PROMPT_KEYWORD, ALL_GT_KEYWORD
      PORTS = range(30021, 30081)
      ...
  ```

- 执行如下指令，进行批量打标

  ```bash
  python gpt_batch_merge.py --model gpt-4o-mini-2024-07-18 --label_file baseline_gt_file.jsonl --output_dir output/batch_merge --failed_dir output/fail_merge
  ```

  - `--model`：GPT模型类型，默认采用`gpt-4o-mini-2024-07-18`；

  - `--label_file`：待打标文件；

  - `--output_dir`：输出文件夹，用于保存每一次请求返回的结果，初次执行必须为**空文件夹**；

  - `--failed_dir`：打标失败的文件保存在该文件夹下。

    **注意：**
    
    - **如果批量打标过程突然中断，重新执行上述指令可继续打标，会跳过已经完成的融合实例**
    - **批量融合日志保存在`log/data_merge.log`**

### 3.3 合并结果

- 合并打标结果和原始信息

  ```
  python tools/merge_result.py --label_file baseline_gt_file.jsonl --result_dir output/batch_merge --merge_file merge_result.csv
  ```

  - `--label_file`：待打标文件；
  - `--result_dir`：上述用于保存打标结果的文件夹路径（`output_dir`）；
  - `--merge_file`：合并文件路径。



## 4. 批量翻译

### 4.1 数据准备（csv或jsonl）

- 准备批量打标的`jsonl`文件，`jsonl`是一种每行包含一个独立的 `JSON `对象的文本文件格式，必须包含的`key`为："`id`"、"`goods_id`"、"`url`"、"`text`"。"`category`"不强制包含，如果没有默认为“None”。

  ```json
  {"id": 1, "category": "dress", "goods_id": 8528627, "url": "https://oss-datawork-cdn.tiangong.tech/xxx.jpg", "text": "The image showcases a xxx."}
  {"id": 2, "category": "dress", "goods_id": 15493424, "url": "https://oss-datawork-cdn.tiangong.tech/xxx.jpg", "text": "The image features an xxx."}
  {"id": 3, "category": "dress", "goods_id": 16755541, "url": "https://oss-datawork-cdn.tiangong.tech/xxx.jpg", "text": "The image showcases an xxx."}
  ```

- 如果你有`csv`文件，同时包含"`id`"、"`goods_id`"、"`url`"、"`text`"信息，可以执行如下指令转换为jsonl文件

  ```bash
  python tools/data_convert.py --csv_file transl_file.csv --json_file transl_file.jsonl --convert_transl
  ```

  - `--csv_file`： 待转换的`csv`文件路径；
  - `--json_file`：转换后保存的`jsonl`文件路径；
  - `--convert_transl`：转换模式，默认转换`csv`文件的"`id`"、"`goods_id`"、"`url`"、"`text`"信息为`jsonl`文件。

### 4.2 批量翻译

- 编辑`prompt/translate_prompt.py`文件，设置`TEMPERATURE`、`MAX_TOKENS`、`USER_PROMPT`和`SYSTEM_PROMPT`等GPT相关参数；

  ```python
  TEMPERATURE = 0.6
  MAX_TOKENS = 4096
  
  SYSTEM_PROMPT = """
  你是一位精通简体中文的翻译专家，熟悉服装设计、服装工艺、服装面料、摄影构图等专业术语，因此对于服装相关的术语使用有深入地理解。你的任务是将以下英语文本翻译成中文。请遵循以下几点要求：
  1）准确翻译服装相关专业术语含义；
  2）翻译后的文本保留原有文本的分段形式和*号加粗格式；
  3）文本翻译自然、流畅和地道，使用优美和高雅的表达方式。"""
  
  USER_PROMPT = "需要翻译的英文文本: text"
  ```

- 编辑`gpt_batch_translate.py`文件中的`PORTS`变量，设置中转服务默认端口号

  ```python
  if __name__ == "__main__":
      from prompt.merge_prompt import SYSTEM_PROMPT, USER_PROMPT, TEMPERATURE, MAX_TOKENS, ALL_GPT_PROMPT_KEYWORD, ALL_GT_KEYWORD
      PORTS = range(30021, 30081)
      ...
  ```

- 执行如下指令，进行批量打标

  ```bash
  python gpt_batch_translate.py --model gpt-4o-mini-2024-07-18 --label_file transl_file.jsonl --output_dir output/batch_transl --failed_dir output/fail_transl
  ```

  - `--model`：GPT模型类型，默认采用`gpt-4o-mini-2024-07-18`；

  - `--label_file`：待打标文件；

  - `--output_dir`：输出文件夹，用于保存每一次请求返回的结果，初次执行必须为**空文件夹**；

  - `--failed_dir`：打标失败的文件保存在该文件夹下。

    **注意：**
    
    - **如果批量打标过程突然中断，重新执行上述指令可继续打标，会跳过已经完成的融合实例**
    - **批量翻译日志保存在`log/data_translation.log`**

### 4.3 合并结果

- 合并打标结果和原始信息

  ```
  python tools/merge_result.py --label_file transl_file.jsonl --result_dir output/batch_translate --merge_file translation_result.csv
  ```

  - `--label_file`：待打标文件；
  - `--result_dir`：上述用于保存打标结果的文件夹路径（`output_dir`）；
  - `--merge_file`：合并文件路径。