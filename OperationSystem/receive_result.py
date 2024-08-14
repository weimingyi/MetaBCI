from kafka import KafkaProducer
import json
from OperationSystem.link_config import LinkConfig



class receive_result:
    def __init__(self):
        self.result_list = []

    def receive_result(self, result):
        self.result = result
        self.result_list.append(self.result)
        print(self.result)
        print(self.result_list)

        # 要发送的数组
        # data_array = list(self.result)
        data_array = [self.result_list, len(self.result_list)]

        # Kafka服务地址
        bootstrap_servers = LinkConfig.Servers
        # Kafka主题
        topic = LinkConfig.Topic1

        # 创建一个生产者实例
        producer = KafkaProducer(bootstrap_servers=bootstrap_servers)

        # 将数组转换为JSON字符串
        data = json.dumps(data_array)

        # 发送数据到Kafka
        future = producer.send(topic, value=data.encode('utf-8'))
        print(future)

        # 等待发送完成
        result = future.get(timeout=60)
        print(result)

        # 关闭生产者
        producer.close()

