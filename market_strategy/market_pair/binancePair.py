#!/usr/bin/python
#coding:utf-8
from market_strategy.market_pair.basePair import BasePair
from concurrent.futures import ThreadPoolExecutor, wait

class BinancePair(BasePair):
    def __init__(self, coin_type, time_type,binance):
        self.coin_type = coin_type
        self.time_type = time_type
        self.threadpool = ThreadPoolExecutor(max_workers=1)
        self.binance =binance
        self.init_own_config()

