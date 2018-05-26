#!/usr/bin/python
#coding:utf-8
import datetime
import decimal
import re
import time

import pytz
from funcat import LLV, HHV, EMA, REF, MA, MACD, CROSS
from funcat.time_series import NumericSeries
from funcat.utils import handle_numpy_warning, FormulaException, rolling_window
import pandas as pd
from sqlalchemy import and_, or_, DECIMAL
from  market_strategy import config
from market_strategy.MyDBSession import MyDBSession
from market_strategy.market_pair.basePair import BasePair
from market_strategy.myLogger import log as logger
import numpy as np
from concurrent.futures import ThreadPoolExecutor, wait
from market_strategy.Order import Order,DBSession

class DoubleBottomMACDPair(BasePair):
    def __init__(self, coin_type, time_type,binance,stop_loss=-0.02):
        self.coin_type = coin_type
        self.time_type = time_type
        self.threadpool = ThreadPoolExecutor(max_workers=1)
        self.strategy_type = config.DoubleBottomMACD
        self.stop_loss = stop_loss
        self.binance = binance
        self.init_own_config()

        #市场竞价-操作
    def __market_broker(self,buy_flag,sell_flag,hashMap, amount, coin_type):
        if(buy_flag):
            logger.debug(self.coin_type+":"+self.time_type+"：买入-broker")
            data=self.binance.get_order_book(symbol=coin_type,limit=5)
            bidPrice=data["bids"][0][0]
            two_str1=data["bids"][0][0][8:]
            two_str2=data["bids"][1][0][8:]
            bool_flag=re.match("00", two_str1) and re.match("00", two_str2)

            bidPrice=float(bidPrice)*(1+0.005)
            if(bool_flag != None):
                bidPrice=round(bidPrice,6)
            else:
                bidPrice=round(bidPrice,8)

            two_str1=data["bids"][0][1][-8:]
            two_str2=data["bids"][1][1][-8:]
            bool_flag=re.match("00000000", two_str1) and re.match("00000000", two_str2)
            if(bool_flag != None):
                amount=amount
            else:
                amount=amount+0.02

            self.buy(bidPrice,coin_type,hashMap,[],amount=amount)
        elif(sell_flag):
            logger.debug(self.coin_type+":"+self.time_type+"：卖出-broker")
            data=self.binance.get_order_book(symbol=coin_type,limit=5)
            askPrice=data["asks"][0][0]
            two_str1=data["asks"][0][0][8:]
            two_str2=data["asks"][1][0][8:]

            bool_flag=re.match("00", two_str1) and re.match("00", two_str2)

            askPrice=float(askPrice)*(1-0.005)
            if(bool_flag != None):
                askPrice=round(askPrice,6)
            else:
                askPrice=round(askPrice,8)

            two_str1=data["asks"][0][1][-8:]
            two_str2=data["asks"][1][1][-8:]
            bool_flag=re.match("00000000", two_str1) and re.match("00000000", two_str2)
            if(bool_flag != None):
                amount=amount
            else:
                amount=amount+0.02
            self.sell(askPrice,[],hashMap, amount=amount,coin_type=coin_type)

    def get_opportunity_double_bottom_macd(self,data):
        #不顾一切
        diff,dea,macd=self.get_MACD(data)
        buy_flag,sell_flag,ma99=self.macd_double_cross(diff,dea,macd,data)

        hashMap={}
        hashMap["average1"]=np.float(dea.series[-1])
        hashMap["average2"]=np.float(dea.series[-2])
        hashMap["ma60_1"]=np.float(ma99.series[-1])
        hashMap["ma60_2"]=np.float(ma99.series[-2])
        hashMap["rate_average"]=hashMap["average1"]/hashMap["average2"]
        hashMap["rate_close"]=0
        if(buy_flag):
            futures = []
            futures.append(self.threadpool.submit(self.__market_broker,buy_flag,sell_flag,hashMap,
                                                 config.min_tx_volume, self.coin_type))
        elif(sell_flag):
            futures = []
            futures.append(self.threadpool.submit(self.__market_broker,buy_flag,sell_flag,hashMap,
                                                config.min_tx_volume, self.coin_type))

    def macd_double_cross(self,diff,dea,macd,data):
        X = np.array(data)
        CLOSE=np.array(X[:,4],dtype=np.float)
        CLOSE = NumericSeries(CLOSE)
        ma99=MA(CLOSE,99)

        jincha=CROSS(diff,dea)
        position_ret=np.where(jincha.series == True)
        lists=list(position_ret[0])
        lists.reverse()
        postion1=None
        postion2=None
        for value in lists:
            dea_obj=dea.series[value]
            if(dea_obj<0):
                if postion1 is None :
                    postion1=value
                else:
                    postion2=value
                    break

        buy_flag=dea.series[postion1]>dea.series[postion2] and CLOSE.series[postion1]<CLOSE.series[postion2]\
                 and postion1-postion2>20 and jincha.series[-1]

        if(buy_flag):
            self.json_save["buy_dea1"]=self.as_num(dea.series[postion1])
            self.json_save["buy_dea2"]=self.as_num(dea.series[postion2])
            self.json_save["buy_close1"]=self.as_num(CLOSE.series[postion1])
            self.json_save["buy_close2"]=self.as_num(CLOSE.series[postion2])

        sicha=CROSS(dea,diff)
        #卖出标志 1.死叉，
        # 2.macd下跌
        sell_falg=sicha.series[-1]

        return buy_flag,sell_falg,ma99


    def get_MACD(self,data,SHORT=12, LONG=26, M=9):
        """
        MACD 指数平滑移动平均线
        """
        X = np.array(data)
        CLOSE=np.array(X[:,4],dtype=np.float)
        CLOSE = NumericSeries(CLOSE)
        DIFF = EMA(CLOSE, SHORT) - EMA(CLOSE, LONG)
        DEA = EMA(DIFF, M)
        MACD = (DIFF - DEA) * 2

        return DIFF,DEA,MACD

    def buy(self,bidPrice,coin_type,hashMap,average_line,amount=config.min_tx_volume):
        order,session=self.save_data_db(bidPrice,amount,coin_type)

    def sell(self, askPirce,average_line,hashMap, coin_type, amount=config.min_tx_volume):
        order,session=self.change_data_db(coin_type,askPirce,amount)

