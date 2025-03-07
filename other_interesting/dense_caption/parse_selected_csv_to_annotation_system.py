import json
import numpy as np
import pandas as pd

# select_images_df = pd.read_csv('/data1/code/dengxinzhe/fg-labelstudio/other_interesting/dense_caption/密集v2.0试标数据 - 衣门襟-试标数据 (1).csv')
select_images_df = pd.read_csv('/data1/code/dengxinzhe/fg-labelstudio/other_interesting/dense_caption/密集v2.0试标数据 - 衣门襟-暗门襟.csv')
select_images_df = pd.read_csv('/data1/code/dengxinzhe/fg-labelstudio/other_interesting/dense_caption/密集v2.0试标数据 - 袖长.csv')
select_images_df = pd.read_csv('/data1/code/dengxinzhe/fg-labelstudio/other_interesting/dense_caption/密集v2.0试标数据 - 袖口 - 1.csv')

target_list = []

for index, item in select_images_df.iterrows():
    
    if item['标签值'] == '拉链开襟':
        pass
        # print(index)
    else:
        pass
        # continue
        
    if pd.isna(item['URL']):
        continue
        
    print(item['标签值'], item['URL'])
    
    sub_dict = {'id': str(index), 
                'pictureList': [
                    {'id': index,
                     'url': item['URL']
                    }
                ]}
    target_list.append(sub_dict)
    
with open(f'denseAnno_test_data_cuff_1th.txt', 'w+', encoding='utf-8') as f:
    json.dump(target_list, f, ensure_ascii=False, indent=2)