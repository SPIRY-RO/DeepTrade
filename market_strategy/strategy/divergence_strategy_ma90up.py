#!/usr/bin/python
#coding:utf-8
import datetime
import pytz
from  market_strategy import config
from market_strategy.MyDBSession import MyDBSession
from market_strategy.market_pair.binancePair import BinancePair
from market_strategy.market_pair.divergenceAverageMa90UpPair import divergenceAverageMa90UpPair
from market_strategy.market_pair.divergenceAveragePair import DivergenceAveragePair
import time
from concurrent.futures import ThreadPoolExecutor, wait, thread
from market_strategy.Order import Order,DBSession
from market_strategy.strategy.base_strategy import StrategyCLI


class DivergenceStrategyCLI(StrategyCLI):
    def __init__(self):
        self.market_pairs = []
        self.market_sell_pairs = []
        self.db_name="market_strategy_divergence_average_ma90up"

    def create_bean(self):
        all_tickers = self.binance.get_all_tickers()
        binance_coin_pairs_30m = all_tickers
        for value_map in binance_coin_pairs_30m:
            symbol=value_map["symbol"]
            if(symbol.find("BTC",2)>0) or self.game_start==False:
                merge_bean = divergenceAverageMa90UpPair(value_map["symbol"],"30m",self.binance)
                merge_bean.config["db_name"]=self.db_name
                self.market_pairs.append(merge_bean)

    def loop(self):
        while(True):
            east8_date = datetime.datetime.fromtimestamp(int(time.time()), pytz.timezone('Asia/Shanghai'))
            self.market_pairs =list(set(self.market_pairs))
            for market_pair in self.market_pairs:
                if(market_pair.time_type == "30m"):
                    mod = east8_date.minute % 30 #时间满足点
                    self.threadpool_30m_run(market_pair)

            time.sleep(config.refresh_rate)


    def market_get_data(self,market_pair):
        data=market_pair.get_history_data()
        market_pair.get_opportunity_divergence_average_ma90up(data)


def main():
    cli = DivergenceStrategyCLI()
    cli.main()

if __name__ == "__main__":
    main()