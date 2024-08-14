import sys

sys.path.append('.')

sys.path.append('..')
import time
from loguru import logger
from AlgorithmSystem.AlgorithmSystemController import AlgorithmSystemControl



if __name__ == "__main__":
    date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    logger.add(sink=fr'./log/stimulation-system-{date}.log', level="INFO", retention='1 week')

    asc = AlgorithmSystemControl()
    asc.run()
