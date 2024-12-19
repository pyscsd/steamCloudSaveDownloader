import os
import logging
import logging.handlers

from . import ver

logger = None

logger_format = '%(asctime)s [%(levelname)s] %(message)s'
logger_datefmt = '%Y-%m-%d %H:%M:%S'
logger_formatter = logging.Formatter(
    fmt=logger_format, datefmt=logger_datefmt)

# Separate Logger
def setup_logger():
    global logger

    logger = logging.getLogger('scsd')
    sh = logging.StreamHandler()
    sh.setFormatter(logger_formatter)
    logger.addHandler(sh)
    logger.info(f'scsd-{ver.__version__} started')
    logger.setLevel(logging.INFO)

setup_logger()

def convert_to_log_level(level:int):
    if (level == 0):
        return logging.ERROR
    elif (level == 1):
        return logging.WARNING
    elif (level == 2):
        return logging.INFO
    else:
        return logging.DEBUG

def setup_logger_post_config(p_filename: str, p_level):
    global logger

    fh = logging.handlers.RotatingFileHandler(
        os.path.join(p_filename),
        maxBytes=10485760, # 10MB
        backupCount=5)
    fh.setFormatter(logger_formatter)
    logger.addHandler(fh)
    logger.setLevel(convert_to_log_level(p_level))

def set_level(p_level: int):
    logger.setLevel(convert_to_log_level(p_level))