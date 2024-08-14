import copy

import numpy as np
import pandas as pd
import scipy
from numba import njit
from scipy import signal

from AlgorithmSystem.AlgorithmImplement.SSVEP.function import EstimateSTEqualizer, firfilter_matrix, iterate_qr, update_inner_product
from AlgorithmSystem.AlgorithmImplement.SSVEP.function import get_result


class CCA(object):
    def __init__(self, target_template_set):
        # 正余弦参考信号
        self.target_template_set = target_template_set

    def recognize(self, data):
        p = []
        data = data.T
        # qr分解,data:length*channel
        [Q_temp, R_temp] = np.linalg.qr(data)
        for template in self.target_template_set:
            template = template[:, 0:data.shape[0]]
            template = template.T
            [Q_cs, R_cs] = np.linalg.qr(template)
            data_svd = np.dot(Q_temp.T, Q_cs)
            [U, S, V] = np.linalg.svd(data_svd)
            rho = 1.25 * S[0] + 0.67 * S[1] + 0.5 * S[2]
            p.append(rho)
        result = p.index(max(p))
        result = result + 1
        judge = pd.Series(p).kurt()
        # print(judge)
        if judge > 4:
            return result, judge
        else:
            return 0, judge


class FastCCA(object):
    def __init__(self, template_list, threshold, min_len, max_len, step, detect_win_num, check_win_num):
        self.step = step
        self.max_len = max_len
        self.min_len = min_len
        self.detect_win_num = detect_win_num
        self.check_win_num = check_win_num
        self.threshold = threshold
        self.template_dict = {}
        self.BP_filter_param = self.__get_bandpass_filter(250)
        self.BP_z0 = signal.lfilter_zi(*self.BP_filter_param)
        # self.PLI_filter_param = signal.iircomb(50, 35, ftype='notch', fs=250)
        # self.PLI_z0 = signal.lfilter_zi(*self.PLI_filter_param)
        template_list = np.asarray(template_list)
        for length in np.linspace(step, max_len, int((max_len - step) / step) + 1):
            # self.template_dict[length] = list(map(self.get_template_q, template_list[:, :, :int(length)]))
            self.template_dict[length] = list(map(self.qr_q, template_list[:, :, :int(length)]))
        # 数据缓存
        self.data_cache = []
        # 滤波器延时缓存
        self.BP_zi_cache = np.copy(self.BP_z0)
        # self.PLI_zi_cache = np.copy(self.PLI_z0)

        self.raw_data = []
        self.cal_flag = False

    def add_data(self, data):
        if len(self.raw_data) == 0:
            self.raw_data = data
            self.cal_flag = False

        else:
            self.raw_data = np.concatenate((self.raw_data, data), axis=1)
            if self.raw_data.shape[1] >= self.min_len:
                if self.cal_flag:
                    # data, self.PLI_zi_cache = signal.lfilter(*self.PLI_filter_param, data, zi=self.PLI_zi_cache)
                    data, self.BP_zi_cache = signal.lfilter(*self.BP_filter_param, data, zi=self.BP_zi_cache)

                    length = self.data_cache[0][0].shape[0]
                    for index in range(self.detect_win_num):
                        if length >= self.max_len:
                            self.data_cache[index] = scipy.linalg.qr_delete(*self.data_cache[index], 0, self.step)
                        le = self.data_cache[index][0].shape[0]
                        self.data_cache[index] = scipy.linalg.qr_insert(*self.data_cache[index], data.T, le)
                else:
                    data = self.raw_data
                    # data, self.PLI_zi_cache = signal.lfilter(*self.PLI_filter_param, data,
                    #                                          zi=np.outer(data[:, 0], self.PLI_z0))
                    data, self.BP_zi_cache = signal.lfilter(*self.BP_filter_param, data,
                                                            zi=np.outer(data[:, 0], self.BP_z0))
                    for index in range(self.detect_win_num):
                        self.data_cache.append(np.linalg.qr(data[:, index * self.step:].T))
                    self.cal_flag = True

    def recognize(self):

        if not self.cal_flag:
            return 0, None
        else:
            result_list, judge_list = self.get_result()
            for index in range(self.detect_win_num-self.check_win_num):
                if np.var(result_list[index:index+self.check_win_num]) == 0 and \
                        len(np.where(np.asarray(judge_list[index:index+self.check_win_num]) > self.threshold)[0]) >= 2:
                    return result_list[index], None

            # result_list, judge_list = self.get_result()
            # counter = np.bincount(result_list)
            # if np.argmax(counter) > 0 and max(counter) >= self.check_win_num:
            #     return np.argmax(counter), None
            return 0, None

    def get_result(self):
        def __cca(template):
            data_svd = np.dot(self.data_cache[index][0].T, template)
            _, s, _ = np.linalg.svd(data_svd)
            rho = 1.25 * s[0] + 0.67 * s[1] + 0.5 * s[2]
            return rho

        result_list = []
        judge_list = []
        for index in range(self.detect_win_num):
            cors = list(map(__cca, self.template_dict[self.data_cache[index][0].shape[0]]))
            predict = cors.index(max(cors)) + 1
            judge = pd.Series(cors).kurt()
            result_list.append(predict)
            judge_list.append(judge)

        return result_list, judge_list

    def clear(self):
        self.data_cache = []
        self.raw_data = []
        self.BP_zi_cache = np.copy(self.BP_z0)
        # self.PLI_zi_cache = np.copy(self.PLI_z0)

    @staticmethod
    def __get_bandpass_filter(samp_rate):
        fs = samp_rate / 2
        N, Wn = signal.ellipord([4 / fs, 90 / fs], [2 / fs, 100 / fs], 3, 40)
        [b1, a1] = signal.ellip(N, 1, 40, Wn, 'bandpass')
        return b1, a1

    @staticmethod
    @njit()
    def qr_q(a):
        q, r = np.linalg.qr(a.T)
        return q


class MultilayerWindowClassifierParameters(object):
    def __init__(self):
        self.window_step = None
        self.max_window_length = None
        self.channels_number = None
        self.equalizer_order = None
        self.template_set = None
        self.detect_win_num = None
        self.check_win_num = None
        self.threshold = None


class MultilayerWindowClassifier(object):
    def __init__(self):
        self.channels_number = None
        self.window_step = None
        self.max_window_length = None
        self.max_window_num = None
        self.equalizer_order = None
        self.template_set = None
        self.template_G1 = None
        self.template_G2 = None
        self.spatio_temporal_equalizer = None
        self.QxQy_inner_product = None
        self.current_index = None
        self.reach_full_window_flag = None
        self.equalized_data_zf = None
        self.equalized_data_R = None
        self.detect_win_num = None
        self.check_win_num = None
        self.threshold = None

    def initial(self, parameters):
        self.window_step = parameters.window_step
        self.max_window_length = parameters.max_window_length
        self.max_window_num = int(self.max_window_length / self.window_step)
        self.channels_number = parameters.channels_number
        self.equalizer_order = parameters.equalizer_order
        self.set_template_set(parameters.template_set)
        self.detect_win_num = parameters.detect_win_num
        self.check_win_num = parameters.check_win_num
        self.threshold = np.copy(parameters.threshold)

        self.clear()

    def update_equalizer(self, noise_data):
        self.spatio_temporal_equalizer = EstimateSTEqualizer(noise_data, self.equalizer_order)

    def add_data(self, new_data):
        if new_data.shape[1] != self.window_step:
            print('error([输入数据长度({})与预定窗长({})不匹配]'.format(new_data.shape[1], self.window_step))

        equalized_new_data = new_data
        # 逐数据块去均值(整体去均值无法迭代)
        new_data = new_data - np.reshape(np.mean(new_data, axis=1), (new_data.shape[0], 1))
        equalized_new_data, self.equalized_data_zf = firfilter_matrix(self.spatio_temporal_equalizer, new_data,
                                                                      self.equalized_data_zf)
        self.equalized_data_R, x_G1, x_G2 = iterate_qr(self.equalized_data_R, equalized_new_data)

        update_inner_product(self.QxQy_inner_product, self.current_index, x_G1, x_G2, self.template_G1, self.template_G2)

        if self.current_index < self.max_window_num:
            self.current_index = self.current_index + 1
            self.reach_full_window_flag = False
        else:
            self.reach_full_window_flag = True

    def get_result(self):
        if not self.reach_full_window_flag:
            max_window = self.current_index - 1
        else:
            max_window = self.current_index

        noise_energy, signal_energy, snr = get_result(self.QxQy_inner_product, max_window, self.window_step)
        # noise_energy_sorted = np.sort(noise_energy, axis=0)
        snr_sorted = np.sort(snr, axis=0)
        # sum_probability = np.sum(np.exp(-0.5 * (noise_energy - noise_energy_sorted[0])), axis=0)
        # th2 = np.asarray([pd.Series(i).kurt() for i in noise_energy.T])
        # th3 = np.asarray([pd.Series(i).kurt() for i in signal_energy.T])
        # aaa = np.argmax(signal_energy, axis=0)
        result = 0
        length = 0
        result_vector = np.zeros(max_window, dtype=int)
        for i in range(max_window):
            judge1 = np.log(np.sum(np.exp(-0.5 * (noise_energy[:, i] - min(noise_energy[:, i]))))) <= 10 ** -int(self.threshold[0])
            judge3 = pd.Series(signal_energy[:, i]).kurt() >= self.threshold[1]
            judge4 = pd.Series(snr[:, i]).kurt() >= self.threshold[1]
            judge5 = ((snr_sorted[-1, i] - snr_sorted[-2, i]) / sum(snr_sorted[:, i])) >= self.threshold[2]
            if judge3:
                result_vector[i] = np.argmax(signal_energy[:, i] / noise_energy[:, i]) + 1

            if i+1 >= self.detect_win_num:
                counter = np.bincount(result_vector[i+1-self.detect_win_num:i+1])
                if np.argmax(counter) > 0 and max(counter) >= self.check_win_num:
                    result = np.argmax(counter)
                    length = i+1

        return result, length

    def clear(self):
        self.reach_full_window_flag = False
        
        self.QxQy_inner_product = np.zeros((40, self.max_window_num, self.channels_number,
                                            self.template_set.shape[1]))
        self.current_index = 1

        # 初始化均衡数据参数
        self.equalized_data_zf = None
        self.equalized_data_R = None

    def set_spatio_temporal_equalizer(self, spatio_temporal_equalizer):
        self.spatio_temporal_equalizer = spatio_temporal_equalizer

    def set_template_set(self, template_set):
        if self.template_set is None:
            self.template_set = template_set

        # 计算模板QR分解
        self.template_G1 = np.zeros((template_set.shape[0], self.max_window_num, self.template_set.shape[1],
                                     template_set.shape[1]))
        self.template_G2 = np.zeros((template_set.shape[0], self.max_window_num, self.window_step,
                                     template_set.shape[1]))

        for template_index in range(0, len(self.template_set)):
            template = self.template_set[template_index]
            template = template[:, 0:self.max_window_length]
            template_extend = np.reshape(np.asarray(template),
                                         (template.shape[0], self.window_step, self.max_window_num), order='F')
            r = None
            for timestep_index in range(0, self.max_window_num):
                r, tg1, tg2 = iterate_qr(r, template_extend[..., timestep_index])
                self.template_G1[template_index, timestep_index] = tg1
                self.template_G2[template_index, timestep_index] = tg2
