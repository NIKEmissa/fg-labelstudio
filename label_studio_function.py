#openai
import os
import os.path as osp
import requests
import json
import base64
#### 小牛翻译
import json
import urllib.error
import urllib.parse
import urllib.request
import pdb

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def call_image_caption(image_path, in_prompt, model="gpt-4o-mini", temperature=0.7):
    system_prompt = "你是一个服装设计大师、服装工艺大师、面料专家、摄影构图专家,时尚杂志排版专家。请按照我的要求描述我提供的电商模特图。"
    if image_path.startswith('http'):
        image = image_path
    elif os.path.splitext(image_path)[1] in ['.jpg', '.png', '.jpeg', '.bmp']:
        # 获取base64字符串encode_image(image_url)
        datas = encode_image(image_path)
        image = f"data:image/jpeg;base64,{datas}"  
        
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
             },
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": in_prompt
                    },
                    {"type": "image_url",
                     "image_url": {"url": image}
                    }
                ]
            }
        ],
        "temperature":temperature
    }
    url = "http://8.219.81.65:30076/proxy-openai"
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"An error occurred: {e}")


def call_merge(in_prompt, model="gpt-4o-mini", temperature=0.7):
    system_prompt = "你是一个语言学家、逻辑学家、服装设计大师、服装工艺大师、面料专家、摄影构图专家,时尚杂志排版专家。请按照我的要求对提供的内容进行富有逻辑行的提取、融合。"
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
             },
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": in_prompt
                    },
                ]
            }
        ],
        "temperature":temperature
    }
    url = "http://8.219.81.65:30066/proxy-openai"
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"An error occurred: {e}")

#key可以自己申请免费的量也很多
def trans_xn(sentence, src_lan='en', tgt_lan='zh', apikey='5aa88d9401927b8a368f4793588d086b'):
    url = 'http://api.niutrans.com/NiuTransServer/translation?'
    data = {"from": src_lan, "to": tgt_lan, "apikey": apikey, "src_text": sentence}
    data_en = urllib.parse.urlencode(data)
    req = url + "&" + data_en
    res = urllib.request.urlopen(req)
    res = res.read()
    res_dict = json.loads(res)
    if "tgt_text" in res_dict:
        result = res_dict['tgt_text']
    else:
        result = res
    return result

# ## 第一次描述
# from IPython.display import Markdown as md
# fas_pmp = call_proxy_openai(fashion_img, in_prompt,model='gpt-4o-mini')
# rt_trans_1 = trans_xn(fas_pmp)
# #款式真值
# design_ele = fashion_prompt.split('.')[0]
# rt_trans_2 = trans_xn(design_ele)
# rt_trans_1 = rt_trans_1.replace('\n\n','<br><br>')
# # 创建 Markdown 表格
# table_md = f"""
# | Initial Caption     | Ground Truth   |
# | ------------------- | ---------------|
# | {rt_trans_1}        | {rt_trans_2}   |
# """
# display(md(table_md))


# ## 第二次融合
# fas_pmp_2, rt_trans_3 = gen_fas_desc(design_ele, fas_pmp, rt_trans_1) 
# # 创建并展示 Markdown 表格
# table_md = f"""
# | Initial Caption     | GT             | Merged Caption |
# | ------------------- | ---------------| ---------------|
# | {rt_trans_1}        | {rt_trans_2}   | {rt_trans_3}   |
# """
# display(md(table_md))

if __name__ == "__main__":
    base_prompt = '''
## Background:
You are a master of fashion design, craftsmanship, fabric expertise, and photographic composition. You excel at providing comprehensive design details by examining images to help users recreate the clothing design through a text-to-image model.

## Definition:
### Design Elements
1. **Garment Categories** - Tops, Bottoms, Dresses, Suits and Sets, Outerwear, Others, Accessories, etc.  
2. **Structure and Cut** - Silhouettes, Cutting Details, Structural Design Elements, etc.  
3. **Function and Technique** - Functional Design, Techniques, etc.  
4. **Detail Design** - Shoulder Types, Neckline and Collar Types, Sleeve Types and Cuffs, Hemlines and Pant Hems, etc.  
5. **Closures and Fastenings** - Closure Types, etc.  
6. **Fabric and Materials** - Fabric Types, Material Properties, Texture and Feel, etc.  
7. **Colors and Patterns** - Colors, Patterns, etc.  
8. **Ornaments and Accessories** - Decorative Elements, Accessories Coordination, etc.  
9. **Target Audience and Context** - Target Audience, Usage Scenarios, etc.  
10. **Sustainable Design** - Sustainable Materials, Sustainable Processes, Carbon Footprint Management, etc.  
11. **Cultural and Emotional Expression** - Cultural Elements, Emotional Expression, etc.  

### Fashion Model Appearance:
1. **Ethnicities:** Caucasian, East Asian, South Asian, Middle Eastern, Black, Latino, Mixed, etc.
2. **Skin Tones:** Fair, Medium, Dark, Tan, etc.
3. **Height:** Tall (approximately 175 cm and above), Medium height (160-175 cm), Petite (below 160 cm), etc.
4. **Body Types:** Slim, Standard, Curvy, Fit, Slender, Curvaceous, etc.
5. **Facial Features:** Defined features, Round face, Oval face, Square face, Pointed chin, High cheekbones, etc.
6. **Makeup Styles:** Natural makeup, Glam makeup, Vintage makeup, Smokey eye makeup, Japanese style makeup, European style makeup, Fresh makeup, etc.
7. **Hairstyles:** Long hair, Short hair, Curly hair, Straight hair, Ponytail, Updo, Braids, Bun, Bangs, etc.
8. **Expressions:** Smiling, Cool, Serious, Happy, Natural, Thoughtful, Playful, Dreamy, Fresh, Elegant, etc.
9. **Accessories:** Necklace, Earrings, Bracelets, Rings, Watch, Sunglasses, Hat, Belt, Bag, Scarf, etc.
10. **Poses:** Standing, Sitting, Kneeling, Walking, Leaning, Looking back, Squatting, Side pose, etc.
11. **Gestures:** Hands on waist, Hands on forehead, Playing with hair, Raising hands, Touching clothes, Kicking, Arms open wide, etc.
12. **Eye Expressions:** Determined, Confident, Soft, Ethereal, Flirtatious, Natural, etc.
13. **Overall Vibe:** Elegant, Cool, Playful, Sweet, Intellectual, Sexy, Edgy, Energetic, Natural, etc.

### Image Background:
1. **Scenes/Settings:** City streets, Indoor studio, Outdoor natural scenery, Beach, Park, Urban skyline, Classical architecture, Modern architecture, Mansion interior, Minimalist background, Industrial background, etc.
2. **Background Colors/Tones:** White, Grey, Black, Pink, Soft warm tones, Cool tones, Gradient background, Solid color background, etc.
3. **Lighting:** Natural light, Soft light, Backlight, Side light, Hard light, Point light source, Light and shadow effects, Flash, Reflector, etc.
4. **Props/Accessories:** Chairs, Tables, Plants, Umbrella, Sofa, Mirror, Picture frame, Books, Suitcase, Bicycle, Wallpaper, Lamps, Photo frames, etc.
5. **Background Details/Decorations:** Paintings, Curtains, Bookshelves, Vases, Wall decor, Rugs, Background plants, Art sculptures, Wall clocks, etc.
6. **Model and Background Relationship:** Model in the foreground, Blurred background, Model blending with background, Model contrasting with background, Combination of foreground and background, Background as part of the story context, etc.

## Goals:
Referring to the [Definition], provide a detailed description of the design element:
1. **场景/环境**：
   - 选择具体的背景，如晴天的城市街道、晚霞下的沙滩、春天阳光明媚的公园、现代建筑内的大堂等。
   - 具体描述场景中的物件和细节，如城市街道上的行人和车辆、室内摄影棚中的道具布置、岸边的椰子树和沙滩椅。
2. **服装风格和剪裁**：
   - 明确服装的整体轮廓和剪裁细节，如A字裙的裙摆宽度和长度、高腰裤的腰线高度、V领上衣的V字深度、茧形大衣的轮廓和肩线设计。
   - 详细描述领口形状、袖型（如灯笼袖、泡泡袖）、下摆形态（如流苏边、荷叶边）、扣子的设计风格等。
3. **面料和质地**：
   - 描述面料类型（如丝绸、羊毛、棉麻混纺）及其表面质地（如粗糙、光滑、柔软）。
   - 在不同光照条件下的展示效果（如柔和窗光下丝绸的光泽、刺眼阳光下亚麻的质感）。
4. **颜色和图案**：
   - 指定衣服的主要色调和搭配色（如用Pantone色号标明）。
   - 对图案的详细描述（如粗细相间的条纹、复古风格的格纹、抽象印花的具体形状和覆盖范围）。
5. **细节设计和装饰元素**：
   - 精确描述装饰元素的位置和样式（如肩部的刺绣图案、袖口的纽扣样式和材质、腰带上的金属扣子）。
   - 强调手工制作的工艺细节，如手工缝制的亮片、刺绣的针法和图样。
6. **服装搭配和整体造型**：
   - 提供明确的搭配建议，展示服装在不同场合（如办公、休闲、宴会）的搭配方式。
   - 明确配饰的材质和风格（如银镯、皮质斜挎包、钻石项链），以及与主要服装的搭配效果。
7. **模特外貌、姿势、表情和动作特征**：
   - 具体描述模特的特征，包括国家、种族、身高、体重、具体肤色、发色和发型。
   - 细化表情和动作（如微笑的弧度、走路的姿态、旋转的方向和速度）。
8. **发型和化妆**：
   - 描述发型的长度、卷曲度和颜色（如长直发、自然卷、波浪卷发，颜色如亚麻金、巧克力棕）。
   - 指定妆容的具体细节（如眼影的颜色、唇彩的质感、腮红的位置和颜色变化），以及与服装的匹配效果。
9. **光影效果和摄影构图**：
   - 指定光源位置、光照强度及方向（如正面光、侧面光、逆光）。
   - 对摄影构图提出具体要求（如三分法、对角线构图、中心对称构图），以及如何突出重点部位。
10. **动态展示和细节特写**：
    - 描述模特的动态动作（如模特旋转时裙摆的飞扬、模特行走时裤脚的摆动）。
    - 强调需要展示的细节特写（如面料的质感、纽扣的切割、刺绣的精细图案）。

## Constrains:
1. **按层次描述：** 从整体到局部，依次描述背景、整体风格、设计元素、面料和材质、以及细节和配件。例如，首先描述背景（如“都市街道”），接着描述服装的整体风格（如“现代风格连衣裙”），然后详细说明主要设计元素（如“红色丝绸，几何图案”），最后是细节和配件（如“金属扣，刺绣”）。
2. **使用客观明确的语言：** 确保描述具体且客观，避免使用主观词汇和情感表达。代替模糊或主观的词语（如“优雅的”），提供具体特征（如“高领设计，简洁大方”）。如需使用感性词汇，需提供明确的解释（如“柔软的丝绸”需注明“丝绸质地光滑，有天然光泽”）。
3. **描述面料和材质：** 明确指出面料类型及其特点，如“这件连衣裙采用纯棉面料，柔软透气，适合夏季穿着”。避免主观评价面料的感受。
4. **标准术语和句式：** 使用标准化的行业术语（如“长袖衬衫”，“蕾丝边领口”），每个句子或段落集中描述一个特征，避免混杂信息。例句：“袖型为长袖，袖口有蕾丝边。”
5. **提供完整的服装描述：** 即使图像只显示局部，仍应给出完整的服装搭配或全身效果描述（如“白色丝绸衬衫搭配黑色及膝裙，红色高跟鞋”）。
6. **包含时间和场合信息：** 在描述中包括适用的时间和场合（如“适合夏季晚宴的红色礼服”），但仅限于服装的实用性和用途，不涉及主观评价。
7. **避免情感和文化背景描述：** 排除情感词汇和文化背景的表达，专注于客观物理特征和具体用途。
8. **简洁和信息量控制：** 确保每个句子都有新的信息，避免重复和冗长。例如：“这件现代风格的**V领连衣裙**采用红色丝绸，面料光滑，长袖设计，配有金属扣装饰。”
9. **使用定量描述：** 尽可能使用定量描述（如尺寸、数量、位置）以增强描述的具体性和精确性。例句：“裙长至膝下，袖子为腕长。”
10. **模特属性：**模特的描述必须包含国家、种族、身高、体重、具体肤色、发色、发型和妆容搭配。
11. **字数限制：**不要输出小标题，将字数限制在350 个 English words.

## Example:
The image shows an **indoor studio setting** with a **minimalist background**. The **walls and floor** are **solid white**, providing a clean, modern look with no additional props or accessories, keeping the focus on the model and the outfit.
The model is wearing a **fitted midi A-line dress** with an **X silhouette**. The dress features **regular shoulders**, a **collarless design**, and a **square neckline**. The **sleeves** are **wrist-length** with **plain cuffs**. It includes a **single-breasted placket**, a **high waist**, and **two front patch pockets** on the chest, each adorned with a **button** and a **dark navy blue contrasting trim**, matching the trim on the neckline.
The dress is made from a **soft knit fabric** that is **slightly stretchy**, offering comfort and flexibility. The fabric has a **smooth texture** with **subtle vertical lines**. The primary color is **off-white**, with **dark navy blue trims** along the neckline, pocket edges, and hemline, creating a distinct contrast. **Four light-colored buttons** are positioned along the chest, providing both functional and decorative elements.
The model is a **Japanese woman** around **25 years old** with **medium-length straight hair**, styled with **bangs**. Her skin tone is **fair**, and she has a **medium height** and a **slim body type**. She stands in a **straight pose** with her hands resting on either side of her waist, emphasizing the dress's fit-and-flare silhouette. Her makeup is **natural**, featuring a **light foundation**, **subtle eye makeup**, and a **nude lip color**.
The lighting is **soft and even**, highlighting the model and the dress without creating harsh shadows. The composition centers the model in the frame, ensuring the dress remains the focal point. The overall presentation clearly showcases the dress's key features: the **fit-and-flare silhouette**, **contrasting trims**, and **decorative buttons**.

## Initialisation：
基于[Background]，聚焦于我的[Goals]，并参考[Definition]，严格遵循[Constrains]，用叙述性英文，如[Examples]中的形式回应我的输入。
'''
    merge_prompt = '''
## Background:
我会在下面的[Context]中提供[服装描述A],[款式真值B]，根据我的要求，需要从[服装描述A]、[款式真值B]中有机的提取相应的设计要素最终组合成一段简洁明了、具备逻辑性的服装文生图提示词。
## Context:
### 服装描述A:ZJ_BASE_CAP
### 款式真值B:ZJ_ALL_OTH
## Definition:
### Design Elements
1. **Garment Categories** - Tops, Bottoms, Dresses, Suits and Sets, Outerwear, Others, Accessories, etc.  
2. **Structure and Cut** - Silhouettes, Cutting Details, Structural Design Elements, etc.  
3. **Function and Technique** - Functional Design, Techniques, etc.  
4. **Detail Design** - Shoulder Types, Neckline and Collar Types, Sleeve Types and Cuffs, Hemlines and Pant Hems, etc.  
5. **Closures and Fastenings** - Closure Types, etc.  
6. **Fabric and Materials** - Fabric Types, Material Properties, Texture and Feel, etc.  
7. **Colors and Patterns** - Colors, Patterns, etc.  
8. **Ornaments and Accessories** - Decorative Elements, Accessories Coordination, etc.  
9. **Target Audience and Context** - Target Audience, Usage Scenarios, etc.  
10. **Sustainable Design** - Sustainable Materials, Sustainable Processes, Carbon Footprint Management, etc.  
11. **Cultural and Emotional Expression** - Cultural Elements, Emotional Expression, etc.  

### Fashion Model Appearance:
1. **Ethnicities:** Caucasian, East Asian, South Asian, Middle Eastern, Black, Latino, Mixed, etc.
2. **Skin Tones:** Fair, Medium, Dark, Tan, etc.
3. **Height:** Tall (approximately 175 cm and above), Medium height (160-175 cm), Petite (below 160 cm), etc.
4. **Body Types:** Slim, Standard, Curvy, Fit, Slender, Curvaceous, etc.
5. **Facial Features:** Defined features, Round face, Oval face, Square face, Pointed chin, High cheekbones, etc.
6. **Makeup Styles:** Natural makeup, Glam makeup, Vintage makeup, Smokey eye makeup, Japanese style makeup, European style makeup, Fresh makeup, etc.
7. **Hairstyles:** Long hair, Short hair, Curly hair, Straight hair, Ponytail, Updo, Braids, Bun, Bangs, etc.
8. **Expressions:** Smiling, Cool, Serious, Happy, Natural, Thoughtful, Playful, Dreamy, Fresh, Elegant, etc.
9. **Accessories:** Necklace, Earrings, Bracelets, Rings, Watch, Sunglasses, Hat, Belt, Bag, Scarf, etc.
10. **Poses:** Standing, Sitting, Kneeling, Walking, Leaning, Looking back, Squatting, Side pose, etc.
11. **Gestures:** Hands on waist, Hands on forehead, Playing with hair, Raising hands, Touching clothes, Kicking, Arms open wide, etc.
12. **Eye Expressions:** Determined, Confident, Soft, Ethereal, Flirtatious, Natural, etc.
13. **Overall Vibe:** Elegant, Cool, Playful, Sweet, Intellectual, Sexy, Edgy, Energetic, Natural, etc.

### Image Background:
1. **Scenes/Settings:** City streets, Indoor studio, Outdoor natural scenery, Beach, Park, Urban skyline, Classical architecture, Modern architecture, Mansion interior, Minimalist background, Industrial background, etc.
2. **Background Colors/Tones:** White, Grey, Black, Pink, Soft warm tones, Cool tones, Gradient background, Solid color background, etc.
3. **Lighting:** Natural light, Soft light, Backlight, Side light, Hard light, Point light source, Light and shadow effects, Flash, Reflector, etc.
4. **Props/Accessories:** Chairs, Tables, Plants, Umbrella, Sofa, Mirror, Picture frame, Books, Suitcase, Bicycle, Wallpaper, Lamps, Photo frames, etc.
5. **Background Details/Decorations:** Paintings, Curtains, Bookshelves, Vases, Wall decor, Rugs, Background plants, Art sculptures, Wall clocks, etc.
6. **Model and Background Relationship:** Model in the foreground, Blurred background, Model blending with background, Model contrasting with background, Combination of foreground and background, Background as part of the story context, etc.

## Goals:
Referring to the [Definition], provide a detailed description of the design element:
1. **场景/环境**：
   - 选择具体的背景，如晴天的城市街道、晚霞下的沙滩、春天阳光明媚的公园、现代建筑内的大堂等。
   - 具体描述场景中的物件和细节，如城市街道上的行人和车辆、室内摄影棚中的道具布置、岸边的椰子树和沙滩椅。
2. **服装风格和剪裁**：
   - 明确服装的整体轮廓和剪裁细节，如A字裙的裙摆宽度和长度、高腰裤的腰线高度、V领上衣的V字深度、茧形大衣的轮廓和肩线设计。
   - 详细描述领口形状（如高领、吊带领）、袖型（如灯笼袖、泡泡袖）、袖口（如介英袖口、螺纹袖口）、开襟方式（如拉链开襟、单排扣开襟）、衣门襟（如拉链开襟、套头开襟）、肩型（如正肩、落肩、插肩）、下摆形态（如流苏边、荷叶边）、扣子、有无口袋及口袋的款式等的设计风格（如休闲时尚、性感、甜美淑女）。
3. **面料和质地**：
   - 描述面料类型（如丝绸、羊毛、棉、麻、混纺、雪纺、合成纤维、再生纤维、皮革等）及其表面质地（如粗糙、光滑、柔软）。
   - 在不同光照条件下的展示效果（如柔和窗光下丝绸的光泽、刺眼阳光下亚麻的质感）。
4. **颜色和图案**：
   - 指定衣服的主要色调和搭配色（如用Pantone色号标明）。
   - 对图案元素的内容、细节形状、位置及排布关系、风格进行详细描述（如粗细相间的黑白条纹、复古风格的蓝色格纹、黑底白色小花、带有绿色叶子的蓝色大花、抽象印花的具体形状及颜色和覆盖范围）。
5. **细节设计和装饰元素**：
   - 精确描述装饰元素的位置和样式（如肩部的刺绣图案、袖口的纽扣样式和材质、腰带上的金属扣子）。
   - 强调手工制作的工艺细节，如手工缝制的亮片、刺绣的针法和图样。
6. **服装搭配和整体造型**：
   - 提供明确的搭配建议，展示服装在不同场合（如办公、休闲、宴会）的搭配方式。
   - 明确配饰的材质和风格（如银镯、皮质斜挎包、钻石项链）和艺术风格（如废土风、小香风、小清新），以及与主要服装的搭配效果。
7. **模特外貌、姿势、表情和动作特征**：
   - 具体描述模特的特征，包括国家、种族、身高、体重、具体肤色、发色和发型。
   - 细化表情和动作（如微笑的弧度、走路的姿态、旋转的方向和速度）。
8. **发型和妆容**：
   - 描述发型的长度、卷曲度和颜色（如长直发、自然卷、波浪卷发，颜色如亚麻金、巧克力棕）。
   - 指定妆容的具体细节（如眼影的颜色、唇彩的质感、腮红的位置和颜色变化），以及与服装的匹配效果。
9. **光影效果和摄影构图**：
   - 指定光源位置、光照强度及方向（如正面光、侧面光、逆光）。
   - 对摄影构图提出具体要求（如三分法、对角线构图、中心对称构图），以及如何突出重点部位。
10. **动态展示和细节特写**：
    - 描述模特的动态动作（如模特旋转时裙摆的飞扬、模特行走时裤脚的摆动）。
    - 强调需要展示的细节特写（如面料的质感、纽扣的切割、刺绣的精细图案）。

## Constrains:
1. 请将我提供的[款式真值B]整理为一句话[款式描述C]，注意不要丢失任何信息；
2. 请将上一步的[款式描述C]全部合并到[服装描述A]中，不能有任何遗漏，合并规则如下：
2.1. 在[服装描述A]和[款式描述C]都出现的内容，保留[服装描述A]的描述；
2.2. 请将[款式描述C]中剩余的内容合并入上一步的结果中，如概念上有冲突，使用[款式描述C]中内容替换；
2.3. 再次对比[服装描述A]和上一步的合并结果，如“buttoned, lace”等特殊描述词没有了，重新合并到结果中
3. 遵循我的[Goals],对合并的内容提取关键设计要素；
4. 按层次描述,从整体到局部，依次描述背景、整体风格（服装设计理念、艺术风格等）、设计元素(包括上装、下装、内搭、外穿)、面料和材质、模特、以及细节和配件。从背景到细节，确保先描述背景，再描述服装整体风格，详细说明设计元素，然后是面料和材质，之后描述一下模特，最后描述细节和配件。例如，首先描述背景（如“都市街道”），接着描述服装的整体风格（如“现代风格连衣裙”），然后详细说明主要设计元素（如“红色丝绸，几何图案”），之后说明模特（如“模特是一位南亚女性，年龄，身高，妆容等”）最后是细节和配件（如“金属扣，刺绣”）；
5. 避免主观解释或情绪化语言，保持描述的客观性和专业性，避免"adding a touch of..." 或 "creating a sense of..." 或"suggests a sense of calm"等；
6. 字数要求在400 english words，当超出字数的时候要删减感觉性描述，保留客观性内容。
'''
    url = 'https://oss-datawork-cdn.tiangong.tech/ai_images/spider/media/1701344885029_289f3ade0e9a4cfcb831b7c800dffe1e.jpg'
    image_caption_en = call_image_caption(url, in_prompt=base_prompt)
    image_caption_cn = trans_xn(image_caption_en).replace('\n\n','<br><br>')

    all_others = {"category":"blouse", "Garment pattern": "Fitted", "Silhouette": "H", "Collar types": "Fungus edge collar", "neckline": "Round", "Sleeve types": "Shirt sleeve", "Cuffs": "Placket",  "Shoulder types": "Regular shoulder", "Garment closure": "Single-breasted", "Pockets": "Pocketless", "Front closure style": "Fully Open Front", "Fabric - Category": "Knitted - Jacquard - Lace"}
    all_others_en = json.dumps(all_others)
    all_others_cn = trans_xn(all_others_en)
    
    case_merge_prompt = merge_prompt.replace('ZJ_BASE_CAP', image_caption_en).replace('ZJ_ALL_OTH', all_others_en)
    merged_caption_en = call_merge(case_merge_prompt)
    merged_caption_cn = trans_xn(merged_caption_en).replace('\n\n', '<br><br>')
    
    pdb.set_trace()



