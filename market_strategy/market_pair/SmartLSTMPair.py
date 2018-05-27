#!/usr/bin/python
#coding:utf-8
from  market_strategy import config
from market_strategy.market_pair.basePair import BasePair
import numpy as np

class SmartLSTMPair(BasePair):
    def __init__(self, coin_type, time_type,binance, stop_loss=-0.02):
        self.coin_type = coin_type
        self.time_type = time_type
        self.strategy_type = config.DivergenceAverage
        self.stop_loss = stop_loss
        self.binance = binance
        self.init_own_config()

    def get_opportunity_SmartLSTM(self,data):
        #不顾一切
        pass


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
