import os
import numpy as np
from math import pi
from PIL import Image, ImageEnhance


def sinusoidal_sample(freqs, phases, srate, frames, stim_color):
    time = np.linspace(0, (frames - 1) / srate, frames)
    color = np.zeros((frames, len(freqs), 3))
    for ne, (freq, phase) in enumerate(zip(freqs, phases)):
        sinw = np.sin(2 * pi * freq * time + pi * phase) + 1
        color[:, ne, :] = np.vstack(
            (sinw * stim_color[0], sinw * stim_color[1], sinw * stim_color[2])
        ).T
    return color

def load_cover(path):
    backlist = []
    cover_list = []
    for name in os.listdir(path):
        book_name = os.path.join(path, name)
        if os.path.isdir(book_name):
            backlist.append(book_name)
    for name_path in backlist:
        image_path = os.path.join(name_path, 'page_1.png')
        cover_list.append(image_path)
    return cover_list


if __name__ == "__main__":

    background_width = 1920
    background_height = 1080
    background_image = Image.new('RGB', (background_width, background_height), (0, 0, 0))

    current_directory = os.getcwd()
    output_images = os.path.join(current_directory, 'output_images')

    n_elements = 8
    symbols = load_cover(output_images)
    stim_pos = [[-720, 270], [-720, -270], [-240, 270], [-240, -270], [240, 270], [240, -270], [720, 270], [720, -270]]

    freqs = np.arange(8, 16, 1)
    phases = np.array([i * 0.35 % 2 for i in range(n_elements)])
    srate = 60
    frames = 4 * srate
    stim_color = [1, 1, 1]

    brightness_values = sinusoidal_sample(freqs, phases, srate, frames, stim_color)

    '''生成目录界面待刺激序列'''
    for sf in range(frames):
        for i in range(n_elements):
            # 读取封面图片
            foreground_image = Image.open(symbols[i])
            # 调节图片大小
            resized_image = foreground_image.resize((300, 400), 3)

            # 创建亮度增强对象
            enhancer = ImageEnhance.Brightness(resized_image)

            # 调整亮度（亮度因子大于1表示增加亮度，小于1表示减少亮度）
            brightened_image = enhancer.enhance(brightness_values[sf, i, 0])

            # 将前景图片粘贴到背景图片的指定位置
            foreground_width, foreground_height = brightened_image.size
            center_x = stim_pos[i][0]
            center_y = stim_pos[i][1]
            left = center_x - foreground_width // 2 + background_width//2
            top = center_y - foreground_height // 2 + background_height//2
            background_image.paste(brightened_image, (left, top))

        # 图片存储至指定位置
        output_path = os.path.join('cover_images', f'{sf}.jpg')
        background_image.save(output_path)

    '''生成目录界面初始化帧'''

    for i in range(n_elements):
        foreground_image = Image.open(symbols[i])
        resized_image = foreground_image.resize((300, 400), 3)

        foreground_width, foreground_height = resized_image.size
        center_x = stim_pos[i][0]
        center_y = stim_pos[i][1]
        left = center_x - foreground_width // 2 + background_width//2
        top = center_y - foreground_height // 2 + background_height//2
        background_image.paste(resized_image, (left, top))

    output_path = os.path.join('cover_images', 'init.jpg')
    background_image.save(output_path)

