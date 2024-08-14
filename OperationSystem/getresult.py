import numpy as np
import copy
from psychopy import visual, core, event, monitors


class getresult:
    def __init__(self):
        self.last_page = None
        self.last_book_id = None
        self.page = 0
        self.book_id = None

        self.id_result = np.arange(0, 8, 1)
        self.page_result = np.arange(8, 14, 1)

        self.result = None
        self.receive_list = []
        self.result_num = -1
        self.back_num = 0

        self.VSObject = None
        self.win = None
        self.trial = None

        self.stim_start_flag = True
        self.result_list = []

    # def close(self, result):

    def co_stim(self):
        # 图书目录闪烁刺激
        frame_num = 0
        while frame_num < 300 or (self.result is None):
            sf = frame_num % self.VSObject.refresh_rate
            self.VSObject.flash_stimuli_co[sf].draw()
            self.win.flip()
            frame_num += 1
        # self.result = None
        # print('co', self.result)


    def re_stim(self):
        id = int(self.trial["id"])
        position = self.VSObject.stim_pos_re[id] + np.array([0, self.VSObject.stim_width_re / 2])
        self.VSObject.index_stimuli.setPos(position)

        # 阅读功能闪烁刺激
        frame_num = 0
        if self.book_id is not None:
            while frame_num < 180 or (self.result is None):
                sf = frame_num % self.VSObject.refresh_rate
                self.VSObject.flash_stimuli_re[sf].draw()
                self.VSObject.pic_read_set[self.book_id][self.page].draw()
                for text_stimulus in self.VSObject.text_stimuli:
                    text_stimulus.draw()
                self.win.flip()
                frame_num += 1
        else:
            self.co_stim()

        self.result = None

    def keep_stim(self):
        id = int(self.trial["id"])
        position = self.VSObject.stim_pos_re[id] + np.array([0, self.VSObject.stim_width_re / 2])
        self.VSObject.index_stimuli.setPos(position)

        # 阅读功能闪烁刺激
        frame_num = 0
        if self.book_id is not None:
            while frame_num < 120:
                sf = frame_num % self.VSObject.refresh_rate
                self.VSObject.flash_stimuli_re[sf].draw()
                self.VSObject.pic_read_set[self.book_id][self.page].draw()
                for text_stimulus in self.VSObject.text_stimuli:
                    text_stimulus.draw()
                self.win.flip()
                frame_num += 1
        else:
            while frame_num < 120:
                sf = frame_num % self.VSObject.refresh_rate
                self.VSObject.flash_stimuli_co[sf].draw()
                self.win.flip()
                frame_num += 1


    def wait_stim(self):
        # initialise index position
        id = int(self.trial["id"])
        position = self.VSObject.stim_pos_re[id] + np.array([0, self.VSObject.stim_width_re / 2])
        self.VSObject.index_stimuli.setPos(position)
        frame_num = 0
        while frame_num < 300:
            self.VSObject.pic_read_set[self.book_id][self.page].draw()
            for text_stimulus in self.VSObject.text_stimuli:
                text_stimulus.draw()
            self.win.flip()
            frame_num += 1

    def back_stim(self, back_result):
        if back_result in self.id_result:
            self.page = self.last_page
            self.book_id = self.last_book_id
            self.re_stim()

        elif back_result in self.page_result:
            # 保持功能
            if back_result == 8 or back_result == 11:
                pass

            # 左翻页功能
            elif back_result == 9:
                if self.page == 0:
                    self.re_stim()
                else:
                    self.page += 1
                    self.re_stim()

            # 右翻页功能
            elif back_result == 12:
                self.page -= 1
                self.re_stim()

            # 回退功能
            elif back_result == 13:
                self.back_num -= 1
                back_result = self.result_list[self.back_num]
                self.get_stim(back_result)

            else:
                pass
        else:
            pass

    def get_stim(self, result):
        self.result_list.append(result)
        self.result_num += 1
        self.back_num = self.result_num

        # 图书目录检索
        if result in self.id_result:
            self.book_id = np.where(self.id_result == result)[0][0]
            self.re_stim()
            self.stim_start_flag = False

        # 阅读功能识别
        elif (result in self.page_result) and (self.book_id is not None):

            # 保持功能
            if result == 8 or result == 11:
                self.wait_stim()

            # 左翻页功能
            elif result == 9:
                if self.page == 0:
                    self.re_stim()
                else:
                    self.page -= 1
                self.re_stim()

            # 右翻页功能
            elif result == 12:
                self.page += 1
                self.re_stim()

            # 回退功能
            elif result == 13:
                self.back_num -= 1
                back_result = self.result_list[self.back_num]
                self.back_stim(back_result)

            else:
                self.stim_start_flag = True
                self.last_page = copy.deepcopy(self.page)
                self.last_book_id = copy.deepcopy(self.book_id)
                self.book_id = None
                self.page = 0
        else:
            pass

    def cur_stim(self, VSObject, win, trial, result):
        self.result = result
        self.VSObject = VSObject
        self.win = win
        self.trial = trial

        if self.stim_start_flag:
            self.co_stim()
        # self.get_stim(self.result)
        # while result != 10:
        #     self.get_stim(self.result)
        self.get_stim(self.result)


        # if self.stim_start_flag:
        #     self.co_stim()
        #     self.stim_start_flag = False
        # else:
        #     self.get_stim(self.result)

