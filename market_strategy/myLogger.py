#coding=utf-8

import logging
import time

import os


class Log:
    def __init__(self):
        self.logname =  'log/' +time.strftime('%Y-%m-%d') + '.log'

    def printconsole(self, level, message):
        # 创建一个logger
        logger = logging.getLogger('mylogger')
        logger.setLevel(logging.DEBUG)
        # 创建一个handler，用于写入日志文件
        if not os.path.exists('log/'):
            os.mkdir('log/')


        fh = logging.FileHandler(self.logname,'a',encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        # 再创建一个handler，用于输出到控制台
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # 定义handler的输出格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        # 给logger添加handler
        logger.addHandler(fh)
        logger.addHandler(ch)
        # 记录一条日志
        if level == 'info':
            logger.info(message)
        elif level == 'debug':
            logger.debug(message)
        elif level == 'warning':
            logger.warning(message)
        elif level == 'error':
            logger.error(message)
        elif level == 'fatal':
            logger.fatal(message)
        logger.removeHandler(ch)
        logger.removeHandler(fh)

    def debug(self,message):
        self.printconsole('debug', message)

    def info(self,message):
        self.printconsole('info', message)

    def warn(self,message):
        self.printconsole('warning', message)

    def error(self,message):
        self.printconsole('error', message)

    def fatal(self,message):
        self.printconsole('fatal', message)


log = Log()
log.info('info msg1000013333')
log.debug('debug msg')
log.warn('warning msg')
log.error('error msg')