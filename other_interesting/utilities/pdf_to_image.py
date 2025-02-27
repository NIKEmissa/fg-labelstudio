import os
import fitz  # PyMuPDF

def pdf_to_images(pdf_path, output_folder):
    # 检查输出文件夹是否存在，如果不存在则创建
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 打开 PDF 文件
    doc = fitz.open(pdf_path)
    
    # 遍历每一页
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)  # 获取页内容
        
        # 转换为图片
        pix = page.get_pixmap()
        
        # 保存为图片文件
        output_path = f"{output_folder}/page_{page_num + 1}.png"
        pix.save(output_path)
        print(f"Page {page_num + 1} saved to {output_path}")

# 设置 PDF 文件路径和输出文件夹
pdf_path = '/data1/code/dengxinzhe/sources/单排扣.pdf'
pdf_path = '/data1/code/dengxinzhe/fg-labelstudio/other_interesting/dense_caption/拉链开襟.pdf'

output_folder = './output_images'

# 转换 PDF 到图片
pdf_to_images(pdf_path, output_folder)
