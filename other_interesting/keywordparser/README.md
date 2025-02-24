# Cloth Item Parser

## 项目概述

本项目旨在解析服装描述文本，并从中提取与最小字段库中的关键字相匹配的条目。通过统计每个关键字的出现次数，提供数据分析的基础。

## 功能

- 从 JSON 文件加载最小字段库。
- 从 TXT 文件读取服装描述数据。
- 提取并统计关键字的出现次数。
- 将结果保存到 CSV 文件中，便于后续分析。

## 依赖

- Python 3.x
- pandas
- collections（Python 内置模块）

## 安装

确保安装了 Python 及相关库。可以通过以下命令安装 pandas：

```bash
pip install pandas
