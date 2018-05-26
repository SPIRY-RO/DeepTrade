#!/usr/bin/python
#coding:utf-8
import datetime
import pytz
from  market_strategy import config
from market_strategy.MyDBSession import MyDBSession
from market_strategy.market_pair.binancePair import BinancePair
from market_strategy.market_pair.doubleBottomPair import DoubleBottomPair
from market_strategy.myLogger import log as logger
import time
from concurrent.futures import ThreadPoolExecutor, wait, thread
from market_strategy.Order import Order,DBSession
from market_strategy.strategy.base_strategy import StrategyCLI


class DoubleBottomStrategyGameCLI(StrategyCLI):
    def __init__(self):
        self.threadpool_5m = ThreadPoolExecutor(max_workers=5)
        self.threadpool_15m = ThreadPoolExecutor(max_workers=3)
        self.threadpool_30m = ThreadPoolExecutor(max_workers=2)
        self.market_pairs = []
        self.market_sell_pairs = []

    def create_bean(self):
        all_tickers = self.binance.get_all_tickers()
        binance_coin_pairs_30m = all_tickers
        for value_map in binance_coin_pairs_30m:
            symbol=value_map["symbol"]
            if(symbol.find("BTC",2)>0):
                merge_bean = DoubleBottomPair(value_map["symbol"],"30m",self.binance)
                merge_bean.init_own_config(db_name=config.db_game)
                self.market_pairs.append(merge_bean)

    def loop(self):
        while(True):
            east8_date = datetime.datetime.fromtimestamp(int(time.time()), pytz.timezone('Asia/Shanghai'))
            for market_pair in self.market_pairs:
                if(market_pair.time_type == "30m"):
                    mod = east8_date.minute % 30 #时间满足点
                    if(mod>27):
                        self.threadpool_30m_run(market_pair)

            time.sleep(config.refresh_rate)


    def sell_threadpool_run(self,market_pair):
        futures = []
        futures.append(self.sell_threadpool.submit(self.__market_get_data,market_pair))
        wait(futures, timeout=20)

    def threadpool_30m_run(self,market_pair):
        futures = []
        futures.append(self.threadpool_30m.submit(self.__market_get_data,market_pair))
        wait(futures, timeout=20)


    def __market_get_data(self,market_pair):
        data=market_pair.get_history_data()
        market_pair.get_opportunity_double_bottom(data)


    def create_waiting_sell_bean(self):
        myDBsession=MyDBSession()
        db_map={"username":config.username,"password":config.password,"ip":config.ip,"db":config.db_game}
        DBSessionClass=myDBsession.getDBSessionClass(db_map)
        session = DBSessionClass()

        #查询有没有买单的
        #时间
        order_result = session.query(Order).filter(Order.type == 0)
        order_list=order_result.all()
        for order in order_list:
            merge_bean = BinancePair(order.coin_type,order.time_type,True)
            self.market_sell_pairs.append(merge_bean)

def main():
    cli = DoubleBottomStrategyGameCLI()
    cli.main()

if __name__ == "__main__":
    main()