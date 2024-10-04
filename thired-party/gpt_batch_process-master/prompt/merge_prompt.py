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
2.4. 要检查合并的内容中[款式描述C]的客观细节是否都保留了，比如涉及到款式、色彩、面料、辅料、材质、纹理、图案、配饰和装饰的内容一定要保留。去处主观感受内容。
3. 遵循我的[Goals],对合并的内容提取关键设计要素；
4. 按层次描述,从整体到局部，依次描述背景、整体风格（服装设计理念、艺术风格等）、设计元素(包括上装、下装、内搭、外穿)、面料和材质、模特、以及细节和配件。从背景到细节，确保先描述背景，再描述服装整体风格，详细说明设计元素，然后是面料和材质，之后描述一下模特，最后描述细节和配件。例如，首先描述背景（如“都市街道”），接着描述服装的整体风格（如“现代风格连衣裙”），然后详细说明主要设计元素（如“红色丝绸，几何图案”），之后说明模特（如“模特是一位南亚女性，年龄，身高，妆容等”）最后是细节和配件（如“金属扣，刺绣”）；
5. 避免主观解释或情绪化语言，保持描述的客观性和专业性，避免"adding a touch of..." 或 "creating a sense of..." 或"suggests a sense of calm"等；
6. 字数要求在400 english words，当超出字数的时候要删减感觉性描述，保留客观性内容。
"""