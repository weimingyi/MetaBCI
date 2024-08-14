import math

# from psychopy import monitors
import numpy as np
from metabci.brainstim.paradigm import (
    READ_SYSTEM,
    SSVEP,
    P300,
    MI,
    AVEP,
    SSAVEP,
    paradigm,
    pix2height,
    code_sequence_generate,
)
from metabci.brainstim.framework import Experiment
from psychopy.tools.monitorunittools import deg2pix


'''自定义'''
import os
from demos.brainstim_demos.re_book_stimconfig import BACKLISTConfig, READ_BOOKConfig, REGISTER_Config
from psychopy import visual, core, monitors
# from OperationSystem.Controlmain import Operation
from OperationSystem.getresult import getresult


from OperationSystem.CommunicationManagement import CommunicationManagement
from OperationSystem.AlgEventHandler import AlgEventHandler
from OperationSystem.EventManager import EventManager
from OperationSystem.link_config import LinkConfig


class Operation:
    def __init__(self):
        # 状态监视器(对应处理端的状态，控制处理的运行)
        # 事件管理器(事件的存入和处理管理)
        self.event_mng = EventManager()
        # 处理端具体的事件处理管理
        self.conManagement2 = CommunicationManagement(self.event_mng, LinkConfig.Topic1, LinkConfig.Topic2)
        self.algeventhandler = AlgEventHandler(self.event_mng, self.conManagement2)


    def run(self):

        self.conManagement2.receive_exchange_message_thread.start()
        self.conManagement2.operator_exchange_message_thread.start()

if __name__ == '__main__':
    operation = Operation()
    operation.run()
