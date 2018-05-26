#!/usr/bin/python
#coding:utf-8
import datetime
import pytz
from  market_strategy import config
from market_strategy.market_pair.VectorTypePair import VectorTypePair
import time
from concurrent.futures import ThreadPoolExecutor
from market_strategy.strategy.base_strategy import StrategyCLI


class VectorTypeStrategyCLI(StrategyCLI):
    def __init__(self):
        self.threadpool_30m = ThreadPoolExecutor(max_workers=1)
        self.market_pairs = []
        self.market_sell_pairs = []
        self.db_name="market_strategy_vector_type"

    def create_bean(self):
        all_tickers = self.binance.get_all_tickers()
        binance_coin_pairs_30m = all_tickers
        for value_map in binance_coin_pairs_30m:
            symbol=value_map["symbol"]
            if(symbol.find("BTC",2)>0):
                merge_bean = VectorTypePair(value_map["symbol"],"30m",self.binance)
                merge_bean.config["db_name"]=self.db_name
                self.market_pairs.append(merge_bean)

    def loop(self):
        while(True):
            east8_date = datetime.datetime.fromtimestamp(int(time.time()), pytz.timezone('Asia/Shanghai'))
            self.market_pairs=list(set(self.market_pairs))
            for market_pair in self.market_pairs:
                self.threadpool_30m_run(market_pair)
                if(market_pair.time_type == "30m"):
                    mod = east8_date.minute % 30 #时间满足点
                    if(mod>27):
                        self.threadpool_30m_run(market_pair)

            time.sleep(config.refresh_rate)


    def market_get_data(self,market_pair):
        data=market_pair.get_history_data()
        market_pair.get_opportunity_vector_type(data)

def main():
    cli = VectorTypeStrategyCLI()
    cli.main()

if __name__ == "__main__":
    main()