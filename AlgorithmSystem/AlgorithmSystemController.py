from loguru import logger
from AlgorithmSystem.AlgorithmImplement.SSVEP.AlgorithmImplementSSVEP import AlgorithmImplementSSVEP
from AlgorithmSystem.Framework.config.SSVEPConfig import SSVEPConfig
from AlgorithmSystem.Framework.AlgorithmSystemManager import AlgorithmSystemManager
from AlgorithmSystem.communication.ReceiveEEGData import ReceiveEEGData
from communication.CommunicationProducer import KafkaProducer


class AlgorithmSystemControl:
    def __init__(self):
        self.algo_sys_mng = None
        # 算法系统是否准备完毕flag
        self.algo_sys_prep_flag = False
        # 接收脑电数据的线程
        self.recv_eeg_data_thread = None
        # Kafka的生产者
        self.producer = None
        # 算法实例
        self.algorithm = None
        # 算法配置文件
        self.config = None

    def run(self):
        if not self.algo_sys_prep_flag:
            self.algo_sys_prep()
        self.algo_sys_mng.run()

    def algo_sys_prep(self):
        # 调用SSVEP的配置文件
        self.config = SSVEPConfig()
        # 创建算法实现实例
        self.algorithm = AlgorithmImplementSSVEP()
        # 创建Kafka生产者
        self.producer = KafkaProducer('A2O')
        self.algo_sys_mng = AlgorithmSystemManager()
        self.algo_sys_mng.initial(self.config, self.algorithm, self.producer)
        # 数据通道数
        channel_num = self.config.channel_num
        # 数据采样点数
        sample_num = self.config.sample_num
        # 脑电数据接收线程启动
        eeg_data_topic = "NEEG"
        self.recv_eeg_data_thread = ReceiveEEGData(eeg_data_topic, self.algo_sys_mng, channel_num, sample_num)
        self.recv_eeg_data_thread.start()
        logger.info(f'开始从{eeg_data_topic}接收脑电数据')
        # 算法启动
        self.algo_sys_prep_flag = True
