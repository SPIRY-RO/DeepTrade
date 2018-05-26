#!/usr/bin/python
#coding:utf-8
import datetime
import decimal
import time

from funcat import LLV, HHV, EMA, REF, MA
from funcat.time_series import NumericSeries
from  market_strategy import config
from market_strategy.market_pair.basePair import BasePair
import numpy as np

class DivergenceAveragePair(BasePair):
    def __init__(self, coin_type, time_type,binance, stop_loss=-0.02):
        self.coin_type = coin_type
        self.time_type = time_type
        self.strategy_type = config.DivergenceAverage
        self.stop_loss = stop_loss
        self.binance = binance
        self.init_own_config()

    def get_opportunity_divergence_average(self,data):
        #不顾一切
        average_data,my_close_list,close_mean_value,my_open_list=self.get_average_line(data);
        bool_data,average_line=self.get_bool_average(average_data)

        if bool_data is None or average_line is None:
            return

        my_close_list=my_close_list.values
        if(len(my_close_list)<2):
            return

        rate_close=my_close_list[-1]/my_close_list[-2]-1

        divergence_average_flag=self.divergence_average(average_line,my_close_list,bool_data)

        sell_flag = np.where( bool_data[-1]<bool_data[-2], True, False)
        self.json_save["rate_close"]=rate_close
        #average 背驰 和 去除 假买点
        buy_flag=divergence_average_flag and rate_close>0.002 and not(self.get_check_average_fake_buy()) \
                    and rate_close<0.006

        #顶背离
        sell_flag = sell_flag


        if(buy_flag):
            self.market_broker(buy_flag,sell_flag,
                               config.min_tx_volume, self.coin_type,average_line)
        elif(sell_flag):
            self.market_broker(buy_flag,sell_flag,
                               config.min_tx_volume, self.coin_type,average_line)
        else:
            self.market_broker(buy_flag,sell_flag,
                               config.min_tx_volume, self.coin_type,average_line)

    def divergence_average(self, average_line,my_close_list,bool_data):
        self.average_line=average_line

        bool_data = NumericSeries(bool_data)
        ref_bool_data = REF(bool_data,1)

        select_bool = bool_data >ref_bool_data
        ret=np.where(select_bool.series==True)[0]

        if select_bool==True:
            first_one_position = ret[-1]
            first_average = average_line[first_one_position]
            first_close = my_close_list[first_one_position]

            second_one_position = ret[-2]
            second_average = average_line[second_one_position]
            second_close = my_close_list[second_one_position]

            #不是底分型，就去除
            high_data=np.array(self.X[:,2],dtype=np.float)
            bottom_up=my_close_list[-1]>high_data[-2]
            #divergence_average 背驰
            flag=first_average <1.5 and second_average<1.5 and  first_average>second_average and first_close< second_close \
                 and bottom_up
            if(flag):
                return True

        self.get_buy_flag_list(ret, average_line, my_close_list)
        return False

    def get_buy_flag_list(self, positions, average_line, my_close_list):
        high_data=np.array(self.X[:,2],dtype=np.float)
        high_data=high_data[-500:]
        self.zhibiao_axis_map["X"]=[]
        self.zhibiao_axis_map["Y"]=[]
        length=len(positions)
        for index in range(length):
            if index -1 >-1:
                first_one_position = positions[index-1]
                first_average = average_line[first_one_position]
                first_close = my_close_list[first_one_position]

                second_one_position = positions[index]
                second_average = average_line[second_one_position]
                second_close = my_close_list[second_one_position]

                bottom_up=second_close>high_data[second_one_position-1]
                flag=first_average>second_average and first_close< second_close \
                     and bottom_up

                if flag:
                    self.zhibiao_axis_map["X"].append(second_one_position)
                    self.zhibiao_axis_map["Y"].append(second_close)
                    self.zhibiao_axis_map["X"].append(first_one_position)
                    self.zhibiao_axis_map["Y"].append(first_close)
