import time

from scipy import signal
import numpy as np

from AlgorithmSystem.AlgorithmImplement.Interface.AlgorithmInterface import AlgorithmInterface
from AlgorithmSystem.AlgorithmImplement.Interface.Model.DataModel import DataModel
from AlgorithmSystem.AlgorithmImplement.SSVEP.algorithm import MultilayerWindowClassifierParameters, MultilayerWindowClassifier, FastCCA
from AlgorithmSystem.AlgorithmImplement.SSVEP.function import EstimateSTEqualizer


class AlgorithmImplementSSVEP(AlgorithmInterface):
    PARADIGMNAME = 'SSVEP'

    def __init__(self):
        super().__init__()
        self.stimulation_frequency_set = [8.0, 8.4, 8.8, 9.2, 9.6, 10, 10.4, 10.8,
                                          12.0, 12.6, 13.2, 13.8, 14.4, 15.0]
        self.channel_no = 8
        self.sample_rate = 250
        self.select_channel = [0, 1, 2, 3, 4, 5, 6, 7]
        self.data_reader = None
        self.ste_classifier = None
        self.cca = None
        self.data_cache = None

        self.cca_flag = True
        self.ste_update_flag = False

        self.all_result = []
        self.report_record = {}
        self.detect_record = {}

        # 虚警相关
        self.result_record = []
        self.last_result = 0
        self.no_call = 0
        self.max_no_call = 5

        # STE相关参数
        self.multi_time = 5
        self.window_step_time = 5 * 0.04
        self.max_window_time = int(100 / 5) * self.window_step_time  # 单位：s
        self.threshold_ste = np.array([10, 5.7, 0.015])
        self.raw_detection_layer = np.array([6, 6])

        self.equalizer_order = [4, 6]
        self.equalizer_update_interval = 250 * 8
        self.equalizer_estimate_length = 250 * 35
        self.detection_layer = self.raw_detection_layer

        self.false_result = []

        # CCA相关参数
        self.step_length = int(self.window_step_time * 250)
        self.min_cal_length = self.step_length * 5
        self.max_cal_length = self.step_length * 18
        self.threshold_cca = 3
        self.win_t = [3, 5]

    def initial(self):
        self.data_reader = DataReader(self.algo_sys_mng, self.select_channel)

        def __get_cs_set(freq):
            temp = [(np.cos(2 * np.pi * samp_point * f) / 500, np.sin(2 * np.pi * samp_point * f) / 500)
                    for f in freq * np.linspace(1, self.multi_time, self.multi_time)]
            return np.asarray(temp).reshape((self.multi_time * 2, len(samp_point)))

        samp_point = np.linspace(0, 1000 / self.sample_rate, 1000, endpoint=False)
        target_template_set = np.array(list(map(__get_cs_set, self.stimulation_frequency_set)))

        parameters = MultilayerWindowClassifierParameters()
        parameters.window_step = int(self.window_step_time * self.sample_rate)
        parameters.max_window_length = int(self.max_window_time * self.sample_rate)
        parameters.channels_number = self.channel_no
        parameters.equalizer_order = self.equalizer_order
        parameters.template_set = target_template_set
        parameters.detect_win_num = self.detection_layer[0]
        parameters.check_win_num = self.detection_layer[1]
        parameters.threshold = np.copy(self.threshold_ste)
        self.ste_classifier = MultilayerWindowClassifier()
        self.ste_classifier.initial(parameters)

        self.cca = FastCCA(target_template_set, self.threshold_cca, self.min_cal_length, self.max_cal_length,
                           self.step_length, self.win_t[1], self.win_t[0])

    def run(self):
        print('\n')
        start = time.time()
        self.initial()
        while True:
            data, block_end, end_flag = self.data_reader.read_data(times=int(self.step_length / 10), pli_filter=True)
            if end_flag:
                # self.__print_result()
                break

            if self.data_cache is None:
                self.data_cache = data
            else:
                self.data_cache = np.hstack((self.data_cache, data))
            # 不应期
            if self.no_call:
                self.no_call -= 1
                continue

            if self.cca_flag:
                result = self.classify_cca(data)
            else:
                if self.ste_update_flag:
                    self.update_ste()
                if self.data_cache.shape[1] >= self.equalizer_estimate_length + self.equalizer_update_interval:
                    self.update_ste(update_from_ste=True)
                result = self.classify_ste(data)

            if result > 0:

                if self.cca_flag:
                    print("CCA report result: {}".format(result))
                else:
                    print("STE report result: {}".format(result))

                self.algo_sys_mng.report(result)
                # self.no_call = self.max_no_call

    def classify_cca(self, data):
        self.cca.add_data(data)
        if self.data_cache.shape[1] > self.equalizer_estimate_length:
            self.update_ste(update_from_cca=True)
            self.cca.clear()
            self.cca_flag = False
            return 0
        result, j = self.cca.recognize()
        if result > 0:
            self.cca.clear()
        return result

    def classify_ste(self, data):
        self.ste_classifier.add_data(data)
        result, win_num = self.ste_classifier.get_result()
        if result > 0:
            self.ste_update_flag = True
            self.ste_classifier.clear()
        return result

    def update_ste(self, update_from_cca=False, update_from_ste=False):
        data = self.data_cache[:, -self.equalizer_estimate_length:-1000]
        equalizer, pi = EstimateSTEqualizer(data, self.equalizer_order)
        self.ste_classifier.set_spatio_temporal_equalizer(equalizer)

        if update_from_ste:
            current_max_window_index = self.ste_classifier.current_index
            window_step = self.ste_classifier.window_step
            cal_data = data[:, -int(window_step * current_max_window_index):]
            self.ste_classifier.clear()
            for i in range(current_max_window_index):
                self.ste_classifier.add_data(cal_data[:, int(i * self.step_length): int((i + 1) * self.step_length)])
        elif update_from_cca:
            self.ste_classifier.clear()
            window_num = min(int(self.cca.raw_data.shape[1] / self.step_length) + 1,
                             int(self.max_window_time / self.step_length))
            cal_data = data[:, -int(self.step_length * window_num)]
            for i in range(window_num):
                self.ste_classifier.add_data(cal_data[:, int(i * self.step_length): int((i + 1) * self.step_length)])

        self.data_cache = data
        self.ste_update_flag = False


class DataReader(object):
    def __init__(self, task, select_channel):
        self.task = task
        self.select_channel = select_channel

        # PLI filter
        self.pli_B, self.pli_A = signal.iircomb(50, 35, fs=250)
        self.pli_z0 = signal.lfilter_zi(self.pli_B, self.pli_A)
        self.pli_zi = None
        # bandpass filter
        self.bp_B, self.bp_A = self.__get_bandpass_filter()
        self.bp_z0 = signal.lfilter_zi(self.bp_B, self.bp_A)
        self.bp_zi = None

    def read_data(self, times=3, pli_filter=True):
        data, end_flag, block_end = self.__get_data()
        if end_flag:
            return None, None, end_flag
        for _ in range(1, times):
            data_temp, end_flag, end_temp = self.__get_data()
            if end_flag:
                return None, None, end_flag
            data = np.concatenate((data, data_temp), axis=1)
            block_end = block_end or end_temp

        if pli_filter:
            return self.__filter(data), block_end, end_flag
        else:
            return data, block_end, end_flag

    def __check_end(self, data):
        trigger = data[-1, :]
        if trigger[np.where(trigger == 243)].shape[0] > 0:
            self.clear()
            block_end = True
        else:
            block_end = False
        return block_end

    def __get_data(self):
        data_model = self.task.get_data()
        while not isinstance(data_model, DataModel):
            data_model = self.task.get_data()
        block_end = self.__check_end(data_model.data)
        data = data_model.data[self.select_channel, :]
        end_flag = data_model.finish_flag
        return data, end_flag, block_end

    def clear(self):
        self.pli_zi = None
        self.bp_zi = None

    def __filter(self, data):
        if self.pli_zi is None:
            data, self.pli_zi = signal.lfilter(self.pli_B, self.pli_A, data, zi=np.outer(data[:, 0], self.pli_z0))
            # data, self.bp_zi = signal.lfilter(self.bp_B, self.bp_A, data, zi=np.outer(data[:, 0], self.bp_z0))
        else:
            data, self.pli_zi = signal.lfilter(self.pli_B, self.pli_A, data, zi=self.pli_zi)
            # data, self.bp_zi = signal.lfilter(self.bp_B, self.bp_A, data, zi=self.bp_zi)
        return data

    @staticmethod
    def __get_bandpass_filter():
        fs = 125
        n, wn = signal.ellipord([6 / fs, 90 / fs], [2 / fs, 100 / fs], 3, 40)
        [b, a] = signal.ellip(n, 1, 40, wn, 'bandpass')
        return b, a
