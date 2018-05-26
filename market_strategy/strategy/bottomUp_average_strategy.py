#!/usr/bin/python
#coding:utf-8
import datetime
import pytz
from  market_strategy import config
from market_strategy.market_pair.BottomUpAveragePair import BottomUpAveragePair
import time
from market_strategy.strategy.base_strategy import StrategyCLI


class BottomUpAverageStrategyCLI(StrategyCLI):
    def __init__(self):
        self.market_pairs = []
        self.market_sell_pairs = []
        self.db_name="bottomUp_average_strategy"
        self.strategy_type=config.DivergenceAverage

    def create_bean(self):
        self.init_db_config(db_name=self.db_name)
        sell_tickers=self.get_waiting_sell(self.config)

        all_tickers = self.binance.get_all_tickers()
        binance_coin_pairs_30m = all_tickers

        config.market_game_start=False
        for value_map in sell_tickers:
            symbol=value_map.coin_type
            if config.market_game_start==False:
                merge_bean = BottomUpAveragePair(value_map.coin_type,"30m",self.binance)
                merge_bean.config["db_name"]=self.db_name
                self.market_pairs.append(merge_bean)
            elif config.market_game_start==True and symbol.find("ETH",2)>0 :
                if symbol.find('BNB')>0:
                    return

                merge_bean = BottomUpAveragePair(value_map.coin_type,"30m",self.binance)
                merge_bean.game_flag=True
                merge_bean.config["db_name"]=self.db_name
                self.market_pairs.append(merge_bean)

        for value_map in binance_coin_pairs_30m:
            symbol=value_map["symbol"]
            if config.market_game_start==False:
                merge_bean = BottomUpAveragePair(value_map["symbol"],"30m",self.binance)
                merge_bean.config["db_name"]=self.db_name
                self.market_pairs.append(merge_bean)
            elif config.market_game_start==True and symbol.find("ETH",2)>0 :
                if symbol.find('BNB')>0:
                    return

                merge_bean = BottomUpAveragePair(value_map["symbol"],"30m",self.binance)
                merge_bean.config["db_name"]=self.db_name
                merge_bean.game_flag=True
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
        if len(data)<500:
            return
        market_pair.get_opportunity_bottomUp_average(data)


def main():
    cli = BottomUpAverageStrategyCLI()
    cli.main()

if __name__ == "__main__":
    main()