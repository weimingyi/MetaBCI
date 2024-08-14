import numpy as np

class BACKLISTConfig:
    n_elements, rows, columns = 8, 2, 4  # n_elements 指令数量;  rows 行;  columns 列
    stim_length, stim_width = 300, 400  # ssvep单指令的尺寸
    stim_color, tex_color = [1, 1, 1], [1, 1, 1]  # 指令的颜色，文字的颜色
    fps = 60  # 屏幕刷新率
    stim_time = 4  # 刺激时长
    stim_opacities = 1  # 刺激对比度
    freqs = np.arange(8, 11, 0.4)  # 指令的频率
    phases = np.array([i * 0.35 % 2 for i in range(n_elements)])  # 指令的相位

class READ_BOOKConfig:
    n_elements, rows, columns = 6, 3, 2  # n_elements 指令数量;  rows 行;  columns 列
    stim_length, stim_width = 200, 150  # ssvep单指令的尺寸
    stim_color, tex_color = [1, 1, 1], [1, 1, 1]  # 指令的颜色，文字的颜色
    fps = 60  # 屏幕刷新率
    stim_time = 4  # 刺激时长
    stim_opacities = 1  # 刺激对比度
    freqs = np.arange(12, 15.1, 0.6)  # 指令的频率
    phases = np.array([i * 0.35 % 2 for i in range(n_elements)])  # 指令的相位
    stim_pos = np.array([[-600, 360], [-600, 0], [-600, -360], [600, 360], [600, 0], [600, -360]])
    symbols = ['保持', '左翻', '目录', '保持', '右翻', '回退']

class REGISTER_Config:
    bg_color = np.array([-1, -1, -1])  # 背景颜色
    display_time = 1  # 范式开始1s的warm时长
    index_time = 0  # 提示时长，转移视线
    rest_time = 0  # 提示后的休息时长
    response_time = 0  # 在线反馈
    port_addr = None  #0xdefc #采集主机端口
    nrep = 1  # block数目
    lsl_source_id = "meta_online_worker"  # None                 # source id
    online = False  # True