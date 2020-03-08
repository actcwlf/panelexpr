import logging
import pathlib


def init_logging(save_path, level=logging.DEBUG):
    p = pathlib.Path(save_path)

    # 主进程运行记录
    # create logger
    logger = logging.getLogger('explorer')
    logger.setLevel(level)

    # create console handler and set level to debug
    ch = logging.FileHandler(filename=str(p.joinpath("monitor.log")))
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    # 中间结果保存记录
    logger = logging.getLogger('intermediate')
    logger.setLevel(level)

    # create console handler and set level to debug
    ch = logging.FileHandler(filename=str(p.joinpath("intermediate.log")))
    ch.setLevel(logging.INFO)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
