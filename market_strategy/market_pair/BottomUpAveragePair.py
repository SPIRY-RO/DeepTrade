#!/usr/bin/python
#coding:utf-8
import datetime
import decimal
import time

from funcat import LLV, HHV, EMA, REF, MA, COUNT
from funcat.time_series import NumericSeries
from  market_strategy import config
from market_strategy.market_pair.basePair import BasePair
import numpy as np
import pandas as pd

class BottomUpAveragePair(BasePair):
    def __init__(self, coin_type, time_type,binance,stop_loss=-0.02):
        self.coin_type = coin_type
        self.time_type = time_type
        self.strategy_type = config.BottomUpAverage
        self.stop_loss = stop_loss
        self.binance = binance
        self.init_own_config()

    def get_opportunity_bottomUp_average(self,data):
        #不顾一切
        average_data,my_close_list,close_mean_value,my_open_list=self.get_average_line(data);
        bool_data,average_line=self.get_bool_average(average_data)

        if bool_data is None or average_line is None:
            return

        my_close_list=my_close_list.values
        if(len(my_close_list)<2):
            return

        rate_close=my_close_list[-1]/my_close_list[-2]-1

        buy_flag=self.get_buy_bottomUp_flag_list()

        sell_flag = np.where( bool_data[-1]<bool_data[-2], True, False)
        self.json_save["rate_close"]=rate_close
        #average 背驰 和 去除 假买点
        buy_flag=   not(self.get_check_average_fake_buy()) \
                     and buy_flag

        #顶背离
        top_down_flag=self.top_flag_position_list[-1] == 499
        self.sell_precondition_satified=not(top_down_flag)
        sell_flag = sell_flag or top_down_flag
        if(buy_flag):
            self.market_broker(buy_flag,sell_flag,
                               config.min_tx_volume, self.coin_type,average_line)


        elif(sell_flag):
            self.json_save["top_down_flag"]=top_down_flag
            self.market_broker(buy_flag,sell_flag,
                               config.min_tx_volume, self.coin_type,average_line)

    def get_buy_bottomUp_flag_list(self):
        intersect1d_list=self.average_axis_buy["X"]

        ref_ma3_1=REF(self.ma3,1)
        ref_ma3_2=REF(self.ma3,2)
        ma3_up_flag=np.where(self.ma3.series[-500:]>ref_ma3_1.series[-500:])
        ma3_down_flag=np.where(ref_ma3_2.series[-500:]>ref_ma3_1.series[-500:])

        right_flag=np.intersect1d(ma3_up_flag,ma3_down_flag)

        X=self.X
        my_close_list=np.array(X[:,4],dtype=np.float)
        my_close_list = pd.Series(my_close_list)
        close_data=np.array(my_close_list)
        close_data = NumericSeries(close_data)

        my_open_list=np.array(X[:,1],dtype=np.float)
        my_open_list = pd.Series(my_open_list)
        open_data=np.array(my_open_list)
        open_data = NumericSeries(open_data)

        columns=np.abs(my_close_list/my_open_list-1)
        columns=columns[-500:]

        wanted_columns1=np.where(0.0005<columns)[0]
        wanted_columns2=np.where(columns<0.005)[0]
        wanted_columns=np.intersect1d(wanted_columns1,wanted_columns2)
        right_flag=np.intersect1d(right_flag,wanted_columns)
        right_flag=np.intersect1d(right_flag,intersect1d_list)

        #高价等差
        hhv_20=HHV(self.ma3,50)
        hhv_rate_list=hhv_20/close_data
        hhv_rate_list=hhv_rate_list.series[-500:]
        hhv_rate_list_flag= np.where(hhv_rate_list > 1.05)
        right_flag=np.intersect1d(right_flag,hhv_rate_list_flag)

        self.zhibiao_axis_map={}
        self.zhibiao_axis_map["X"]=right_flag
        my_close_list=my_close_list.values[-500:]
        self.zhibiao_axis_map["Y"]=my_close_list[right_flag]

        numbers_columns = {}
        numbers_columns["X"]=np.where(columns>0.01)[0]
        numbers_columns["Y"]=my_close_list[numbers_columns["X"]]
        numbers_columns["Z"]=columns.values[numbers_columns["X"]]
        self.additional_map_list.append(numbers_columns)
        self.get_top_flag_position_list()
        if len(right_flag) > 0 :
            flag=right_flag[-1]==499
            return flag

        return False
