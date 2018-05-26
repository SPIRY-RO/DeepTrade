#!/usr/bin/python
#coding:utf-8
import datetime
from threading import Thread

import pytz
from  market_strategy import config
from market_strategy.market_pair.binancePair import BinancePair
from market_strategy.myLogger import log as logger
import time
from concurrent.futures import ThreadPoolExecutor, wait, thread
from market_strategy.Order import Order,DBSession
from market_strategy.strategy.base_strategy import StrategyCLI


class AverageStrategyCLI(StrategyCLI):
    def __init__(self):
        self.threadpool_5m = ThreadPoolExecutor(max_workers=config.threadpool_5m_worker)
        self.threadpool_15m = ThreadPoolExecutor(max_workers=config.threadpool_15m_worker)
        self.threadpool_30m = ThreadPoolExecutor(max_workers=config.threadpool_30m_worker)
        self.market_pairs = []
        self.market_sell_pairs = []
        self.sell_threadpool = ThreadPoolExecutor(max_workers=3)
        self.strategy_type = config.AverageStrategy
        self.db_name="market_average"

    def main(self):
        logger.debug("main")
        self.get_binance()
        self.create_bean()
        try :
            self.loop()
        except Exception as  e:
            logger.fatal("宕机了。。。。。。。。。")
            logger.fatal(e)
            main()

    def create_bean(self):
        all_tickers = self.binance.get_all_tickers()
        binance_coin_pairs_30m = all_tickers
        for value_map in binance_coin_pairs_30m:
            symbol=value_map["symbol"]
            if(symbol.find("ETH",2)>0):
                merge_bean = BinancePair(value_map["symbol"],"30m",self.binance)
                merge_bean.config["db_name"]=self.db_name
                self.market_pairs.append(merge_bean)

    def loop(self):
        while(True):
            east8_date = datetime.datetime.fromtimestamp(int(time.time()), pytz.timezone('Asia/Shanghai'))
            mod = east8_date.minute % 5 #时间满足点

            for market_pair in self.market_pairs:
                self.threadpool_30m_run(market_pair)
                if(market_pair.time_type == "30m"):
                    mod = east8_date.minute % 30 #时间满足点
                    if(mod>27):
                        self.threadpool_30m_run(market_pair)

            time.sleep(config.refresh_rate)

    def market_get_data(self,market_pair):
        data=market_pair.get_history_data()
        try:
            market_pair.get_opportunity(data)
        except Exception as e :
            logger.fatal(self.coin_type+":"+e)
            pass

def main():
    cli = AverageStrategyCLI()
    cli.main()

if __name__ == "__main__":
    main()