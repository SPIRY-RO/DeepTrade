#!/usr/bin/python
#coding:utf-8
import datetime
import decimal
import time

from  market_strategy import config
import numpy as np

from market_strategy.market_pair.divergenceAveragePair import DivergenceAveragePair


class divergenceAverageMa90UpPair(DivergenceAveragePair):
    def __init__(self, coin_type, time_type,binance,stop_loss=-0.02):
        self.coin_type = coin_type
        self.time_type = time_type
        self.strategy_type = config.DivergenceAverageMA90Up
        self.stop_loss = stop_loss
        self.binance = binance
        self.init_own_config()

    def get_opportunity_divergence_average_ma90up(self,data):
        #不顾一切
        average_data,my_close_list,close_mean_value,my_open_list=self.get_average_line(data);
        bool_data,average_line=self.get_bool_average(average_data)

        if bool_data is None or average_line is None:
            return

        rate_average=average_line[-1]/average_line[-2]-1
        my_close_list=my_close_list.values
        if(len(my_close_list)<2):
            return

        rate_close=my_close_list[-1]/my_close_list[-2]-1

        sell_flag = np.where( bool_data[-1]<bool_data[-2], True, False)

        buy_flag = np.where( bool_data[-1]>bool_data[-2], True, False)
        
        hashmap=self.json_save
        hashmap["rate_close"]=rate_close
        hashmap["rate_average"]=rate_average
        hashmap["ma90_1"]=np.float(round(self.ma90.series[-1],6))
        hashmap["ma90_2"]=np.float(round(self.ma90.series[-2],6))
        hashmap["average1"]=np.float(round(average_line[-1],6))
        hashmap["average2"]=np.float(round(average_line[-2],6))
        #average 拉升
        buy_flag=buy_flag  and hashmap["ma90_1"]>hashmap["ma90_2"] and not(self.get_check_average_fake_buy()) \
                 and rate_close>0.001 and rate_close<0.006

        sell_flag = sell_flag or self.get_top_down_flag(my_close_list)
        if(buy_flag):
            self.market_broker(buy_flag,sell_flag,
                               config.min_tx_volume, self.coin_type,average_line)

        elif(sell_flag):
            self.market_broker(buy_flag,sell_flag,
                               config.min_tx_volume, self.coin_type,average_line)


