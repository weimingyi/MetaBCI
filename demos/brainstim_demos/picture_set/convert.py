import fitz  # PyMuPDF
from pathlib import Path

def find_pdf_files(file_path):
    pdf_files = []
    for path in Path(file_path).rglob('*.pdf'):
        pdf_files.append(str(path))
    return pdf_files

def get_pic_set(file_path, output_path):
    pic_set = file_path.replace('.pdf', '')
    set_name = pic_set.split('\\')[-1]
    set_path = output_path / set_name
    return set_path, set_name

def pdf_to_images(pdf_path, output_path):
    """
    将PDF的每一页转换为图片，并保存到指定的文件夹中。

    :param pdf_path: PDF文件的路径
    :param output_folder: 输出图片的文件夹路径
    """
    pic_set_path, pic_set_name = get_pic_set(pdf_path, output_path)

    output_images_path = Path(output_path)
    pdf_path = Path(pdf_path)
    pic_set_path = Path(pic_set_path)

    # 确保输出文件夹存在
    if not output_path.exists():
        output_path.mkdir(parents=True)

    # 创建一个当前pdf的图片转换存储文件夹
    try:
        pic_set_path.mkdir(parents=True, exist_ok=True)
        print(f"文件夹 '{pic_set_name}' 创建成功")
    except FileExistsError:
        print(f"文件夹 '{pic_set_name}' 已存在")
    except Exception as e:
        print(f"创建文件夹时发生错误: {e}")

    # 打开PDF文件
    doc = fitz.open(pdf_path)

    # 遍历PDF的每一页
    for page_num in range(len(doc)):
        # 加载页面
        page = doc.load_page(page_num)
        # 获取页面的pixmap表示，这里使用PNG格式
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)

        # 保存到文件
        pic_path = pic_set_path.joinpath(f"page_{page_num + 1}.jpg")
        pix.save(str(pic_path))

        # 释放pixmap对象占用的内存
        pix = None

        # 关闭PDF文件
    doc.close()

if __name__ == '__main__':
    # 使用示例
    current_directory = Path.cwd()
    pdf_path = current_directory / 'ori_pdf'
    output_images = current_directory / 'output_images'

    file_path = pdf_path
    pdf_files = find_pdf_files(file_path)
    for path in pdf_files:
        pdf_to_images(path, output_images)
