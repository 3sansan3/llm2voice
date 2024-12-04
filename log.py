import logging
import sys
from typing import Optional
from datetime import datetime

class Logger:
    def __init__(self):
        self.logger = logging.getLogger('AIPromate')
        self.logger.setLevel(logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 格式化器 - 修改时间格式以支持毫秒
        formatter = logging.Formatter(
            '%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)

    def info(self, message: str, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)

    def error(self, message: str, exc_info: Optional[Exception] = None):
        if exc_info:
            self.logger.error(message, exc_info=True)
        else:
            self.logger.error(message)

    def debug(self, message: str):
        self.logger.debug(message)

    def warning(self, message: str):
        self.logger.warning(message)

log = Logger()

# 使用示例
if __name__ == "__main__":
    log.debug("这是一条调试信息")
    log.info("这是一条普通信息")
    log.warning("这是一条警告信息")
    log.error("这是一条错误信息")
    log.critical("这是一条严重错误信息")