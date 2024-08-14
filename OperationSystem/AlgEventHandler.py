from loguru import logger
import numpy as np
from OperationSystem.getresult import getresult
from OperationSystem.receive_result import receive_result
'''自定义'''
import os
import keyboard
import copy

class AlgEventHandler:
    def __init__(self, event_mng, conmanager):
        self.exchange_message_management = conmanager
        event_mng.AddEventListener('stim', self.do_stim)  # 向事件处理器中添加event和对应的处理函数
        # event_mng.AddEventListener('XQXQ', self.do_XQXQ)
        self.receive_result = receive_result()
        event_mng.Start()

    def do_XQXQ(self, event):
        # 正常运行
        msg = event.message
        if msg:
            self.result = msg['result']
            logger.info("系统判决结果为：" + str(self.result))
            self.receive_result.receive_result(self.result)

    def do_stim(self, result, event):
        # 连接测试模式
        self.result = result
        logger.info("系统判决结果为：" + str(self.result))
        self.receive_result.receive_result(self.result)


