import pandas as pd

df = pd.read_csv('/data1/code/dengxinzhe/sources/密集v2.0试标数据 - 衣门襟-试标数据.csv')

tgt_df = df[df['标签值'] == '单排扣开襟']

tgt_list = []

for index, item in tgt_df.iterrows():
    # print(index, item['URL'])
    
    sub_dict = {'id':index, 
                'pictureList': [
                    {'id':index,
                     'url':item['URL']
                    }
                ]}
    
    # print(sub_dict)
    
    tgt_list.append(sub_dict)
    
import json

# 打开文件并写入数据
with open('output.txt', 'w', encoding='utf-8') as f:
    json.dump(tgt_list, f, ensure_ascii=False, indent=2)    