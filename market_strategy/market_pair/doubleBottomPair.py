#!/usr/bin/python
#coding:utf-8
import datetime
import decimal
import re
import time

import pytz
from funcat import LLV, HHV, EMA, REF, MA
from funcat.time_series import NumericSeries
from funcat.utils import handle_numpy_warning, FormulaException, rolling_window
import pandas as pd
from sqlalchemy import and_, or_, DECIMAL
from  market_strategy import config
from market_strategy.market_pair.basePair import BasePair
from market_strategy.myLogger import log as logger
import numpy as np
from concurrent.futures import ThreadPoolExecutor, wait
from market_strategy.Order import Order,DBSession

class DoubleBottomPair(BasePair):
    def __init__(self, coin_type, time_type,binance,stop_loss=-0.02):
        self.coin_type = coin_type
        self.time_type = time_type
        self.threadpool = ThreadPoolExecutor(max_workers=1)
        self.strategy_type = config.DoubleBottomAverage
        self.stop_loss = stop_loss
        self.binance = binance
        self.init_own_config()

    def get_opportunity_double_bottom(self,data):
        #不顾一切
        average_data,my_close_list,close_mean_value,my_open_list=self.get_average_line(data);
        bool_data,average_line=self.get_bool_average(average_data)

        if average_line is None or len(average_line)==0:
            return

        rate_average=average_line[-1]/average_line[-2]-1
        my_close_list=my_close_list.values
        rate_close=my_close_list[-1]/my_close_list[-2]-1
        k5_close_list=my_close_list[-5:]
        k5_open_list=my_open_list[-5:]

        # buy_flag = np.where(average_line[-1]<config.average_line_buy and bool_data[-1]>bool_data[-2]
        #                     and mean_value >my_close_list[-1]
        #                     , True, False)

        double_cross_flag=self.double_cross(average_line,average_data,bool_data)

        sell_flag = np.where( bool_data[-1]<bool_data[-2], True, False)
        k5_flag_list=np.where( k5_close_list<k5_open_list)
        flag_size=k5_flag_list[0].size
        average_line_20=average_line[100-20:]
        hashmap=self.json_save
        hashmap["rate_close"]=rate_close
        hashmap["rate_average"]=rate_average
        hashmap["ma90_1"]=np.float(round(self.ma90.series[-1],6))
        hashmap["ma90_2"]=np.float(round(self.ma90.series[-2],6))
        hashmap["average1"]=np.float(round(average_line[-1],6))
        hashmap["average2"]=np.float(round(average_line[-2],6))
        ma60_flag=hashmap["ma90_1"]   > hashmap["ma90_2"]
        #专做上升段  #ma60上升
        buy_flag=double_cross_flag and my_close_list[-1]>hashmap["ma90_1"] and ma60_flag\
                  and hashmap["rate_close"]>0.002 and not(self.get_check_average_fake_buy)

        top_down_flag=self.get_top_down_flag(my_close_list)
        sell_flag = sell_flag and rate_close<0 and not( rate_close>0 and rate_average<0) \
                    or  hashmap["ma90_1"]   < hashmap["ma90_2"] or top_down_flag
        if(buy_flag):
            self.market_broker(buy_flag,sell_flag,
                               config.min_tx_volume, self.coin_type,average_line)
        elif(sell_flag):
            self.market_broker(buy_flag,sell_flag,
                               config.min_tx_volume, self.coin_type,average_line)

    def double_cross(self, average_line,average_data,bool_data):
        bool_data = NumericSeries(bool_data)
        ref_bool_data = REF(bool_data,1)

        select_bool = bool_data >ref_bool_data
        select_bool=select_bool.series[99-20:]
        ret=np.where(select_bool==True)
        size=ret[0].size

        if(size<2):
            return False

        average_line=average_line[100-20:]
        first_one_position = ret[0][-1]
        first_one = average_line[first_one_position]

        second_one_position = ret[0][-2]
        second_one = average_line[second_one_position]

        if(first_one>second_one and select_bool[-1]==True):
            return True

        return False
