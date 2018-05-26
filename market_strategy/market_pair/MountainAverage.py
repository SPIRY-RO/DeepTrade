#!/usr/bin/python
#coding:utf-8
import datetime
import decimal
import time

from funcat import HHV, REF, MIN
from funcat.time_series import NumericSeries

from  market_strategy import config
from market_strategy.market_pair.basePair import BasePair
import numpy as np

class MountainAverage(BasePair):
    def __init__(self, coin_type, time_type,binance, stop_loss=-0.05):
        self.coin_type = coin_type
        self.time_type = time_type
        self.strategy_type = config.MountainAverage
        self.stop_loss = stop_loss
        self.binance = binance
        self.init_own_config()

    def get_opportunity_mountain_average(self,data):
        #不顾一切
        average_data,my_close_list,close_mean_value,my_open_list=self.get_average_line(data);
        bool_data,average_line=self.get_bool_average(average_data)

        if bool_data is None or average_line is None:
            return

        my_close_list=my_close_list.values
        if(len(my_close_list)<2):
            return

        #average 背驰 和 去除 假买点

        self.get_top_flag_position_list()
        buy_flag=self.getMountainAverage(my_close_list)
        #顶背离
        #top_down_flag=self.get_top_down_flag(my_close_list)
        #self.sell_precondition_satified=not(top_down_flag)
        #sell_flag = sell_flag or top_down_flag

        #1.是average的买点 x   2.对于前一地点有了较大的拉升（0.25）
        #3.average 前一买点是低于0.5的
        sell_flag=self.get_sell_flag(average_line)

        if(buy_flag):
            self.market_broker(buy_flag,sell_flag,
                               config.min_tx_volume, self.coin_type,average_line)
        elif(sell_flag):
            self.market_broker(buy_flag,sell_flag,
                               config.min_tx_volume, self.coin_type,average_line)
        else:
            self.market_broker(buy_flag,sell_flag,
                               config.min_tx_volume, self.coin_type,average_line)

    def getMountainAverage(self,my_close_list):
        temp=NumericSeries(self.average_axis_buy["Z"])
        ref_temp=REF(temp,1)
        size=ref_temp.series.size
        if(size<1):
            return False
        temp=temp.series[-size:]
        temp_average=self.average_data.series[-500:]
        buy_axis={}
        buy_axis["X"]= []
        buy_axis["Y"]=[]
        buy_axis["Z"]=[]
        #找出买点
        point_save=0

        for i in range(size):
            if i +1 <=size and i>=point_save:
                i1=self.average_axis_buy["X"][i]
                value_i1=temp[i]

                for j in range(i+1,size):
                    j1=self.average_axis_buy["X"][j]
                    value_j1=temp[j]
                    gap_length=j1-i1
                    if(gap_length<100 and gap_length>20):
                        gap_abs=np.abs(value_i1-value_j1)
                        if(gap_abs<0.08):
                            #找出两点之间最高值
                            temp_y=temp_average[i1:j1]
                            temp_area=sum(temp_y)-value_i1*(len(temp_y)-2)

                            if temp_area>0:
                                buy_axis["X"].append(i1)
                                buy_axis["X"].append(j1)
                                buy_axis["Y"].append(value_i1)
                                buy_axis["Y"].append(value_j1)
                                buy_axis["Z"].append(temp_area)
                                buy_axis["Z"].append(temp_area)
                                point_save=j
                            break

        if len(buy_axis["X"])==0:
            return False

        temp_map={}
        temp_map["X"]=np.array(buy_axis["X"])
        temp_map["Y"]=temp_average[temp_map["X"]]
        temp_map["Z"]=np.array(buy_axis["Z"])
        temp_map["C"]="#0A0A0A"
        self.additional_average_map_list.append(temp_map)
        temp_map2={}
        temp_map2["X"]=temp_map["X"]
        temp_map2["Y"]=my_close_list[temp_map2["X"]]
        self.zhibiao_axis_map=temp_map2

        if temp_map["X"].size>0 and temp_map["X"][-1]==499 :
            return True

        return False

    def get_sell_flag(self,average_line):
        ref_average=REF( self.average_data,1)

        temp_flag=self.average_data<ref_average
        temp_flag=temp_flag.series[-500:]
        positions=np.where(temp_flag==True)[0]
        temp={}
        temp["X"]=positions
        temp["Y"]=average_line[positions]
        temp["C"]="#7FFF00"
        self.additional_average_map_list.append(temp)

        if positions[-1] == 499:
            return True

        return False

