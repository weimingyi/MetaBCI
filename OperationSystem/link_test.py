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

    # 刺激系统会接收最后一次发送的结果，功能检测时将所测功能取消注释并重新执行代码即可
    # 进入检测
    operation.algeventhandler.do_stim(3, event=None)
    # 右翻检测
    operation.algeventhandler.do_stim(12, event=None)
    # 左翻检测
    operation.algeventhandler.do_stim(9, event=None)
    # 保持检测
    operation.algeventhandler.do_stim(11, event=None)
    # 回退检测
    operation.algeventhandler.do_stim(13, event=None)
    # 返回菜单检测
    operation.algeventhandler.do_stim(10, event=None)







