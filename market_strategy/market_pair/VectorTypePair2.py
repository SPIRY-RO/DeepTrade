#!/usr/bin/python
#coding:utf-8
import datetime
import decimal
import re
import time

from funcat import MA
from funcat.time_series import NumericSeries

from market_strategy.market_pair.basePair import BasePair
from concurrent.futures import ThreadPoolExecutor, wait
from market_strategy import config
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.finance as mpf

import time

class VectorTypePair2(BasePair):
    def __init__(self, coin_type, time_type,binance,stop_loss=-0.02):
        self.coin_type = coin_type
        self.time_type = time_type
        self.threadpool = ThreadPoolExecutor(max_workers=1)
        self.strategy_type = config.VectorType
        self.stop_loss = stop_loss
        self.binance = binance
        self.init_own_config()
        self.config["db_name"]="market_strategy_vector_type_2"


    def get_opportunity_vector_type(self,data):
        X = np.array(data)
        self.X=X
        k_data,time_list = self.get_Fnk(X)
        ## 判断包含关系
        after_fenxing=self.get_relation(k_data)
        fenxing_data,fenxing_plot,fenxing_type=self.find_top_bottom(after_fenxing,time_list)
        buy_flag=fenxing_plot[-1]>fenxing_plot[-2] and fenxing_plot[-2] < fenxing_plot[-3] \
                 and (fenxing_plot[-1]-fenxing_plot[-2])/fenxing_plot[-2] <0.05
        sell_flag=fenxing_plot[-1]<fenxing_plot[-2]
        average_line={}
        self.json_save["fenxing_plot"]=fenxing_plot
        self.json_save["fenxing_type"]=fenxing_type
        if(buy_flag):
            self.market_broker(buy_flag,sell_flag, config.min_tx_volume, self.coin_type,average_line)
        elif(sell_flag):
            self.market_broker(buy_flag,sell_flag, config.min_tx_volume, self.coin_type,average_line)

    def get_Fnk(self,X,n=3):
        data={}
        data["open"]=np.array(X[:, 1], dtype=np.float)[-500:]
        data["close"]=np.array(X[:, 4], dtype=np.float)[-500:]
        data["high"]=np.array(X[:, 2], dtype=np.float)[-500:]
        data["low"]=np.array(X[:, 3], dtype=np.float)[-500:]
        k_data = pd.DataFrame(data)

        self.ma90 = MA(NumericSeries(data["close"]),90)
        self.ma3 = MA(NumericSeries(data["close"]),3)
        time_list=[]
        for my_time in X[:, 6]:
            # timestamp转化为struct_time结构
            x = time.localtime(int(my_time)/1000)
            # 将struct_time按一定格式输出为string
            real_time = time.strftime('%Y-%m-%d %H:%M:%S', x)
            my_time=real_time
            time_list.append(real_time)

        Fnk = pd.DataFrame()
        length=len(time_list)+1
        for i in range(n,length,n):
            temp = k_data[i-n : i] #拿五个
            temp_open =  np.mean(temp.open)
            temp_high = np.mean(temp.high)
            temp_low = np.mean(temp.low)
            temp_k = temp[-1:]
            temp_k.open = temp_open
            temp_k.high = temp_high
            temp_k.low = temp_low
            Fnk = pd.concat([Fnk,temp_k],axis = 0)

        #把最后的一根K线载入，单独处理
        last_one=k_data[-1:]
        temp_open = last_one.open.values[-1]
        temp_high = max(last_one.high)
        temp_low = min(last_one.low)
        temp_k = last_one[-1:]
        temp_k.open = temp_open
        temp_k.high = temp_high
        temp_k.low = temp_low
        Fnk = pd.concat([Fnk,temp_k],axis = 0)
        return Fnk,time_list

    def middle_num(self,k_data):
        # 鸡肋函数，完全的强迫症所为，只为下面画图时candle图中折线时好看而已 - -！
        # k_data 为DataFrame格式
        plot_data=[]
        for i in range(len(k_data)):
            temp_y = (k_data.high.values[i]+k_data.low.values[i])/2.0
            plot_data.append(temp_y)
        return plot_data

    def get_relation(self,k_data):
        ## 判断包含关系
        after_fenxing = pd.DataFrame()
        temp_data = k_data[:1]
        zoushi = [3] # 3-持平 4-向下 5-向上
        print(temp_data.high)
        for i in range(len(k_data)):
            case1_1 = temp_data.high.values[-1] > k_data.high.values[i] and temp_data.low.values[-1] < k_data.low.values[i]# 第1根包含第2根
            case1_2 = temp_data.high.values[-1] > k_data.high.values[i] and temp_data.low.values[-1] == k_data.low.values[i]# 第1根包含第2根
            case1_3 = temp_data.high.values[-1] == k_data.high.values[i] and temp_data.low.values[-1] < k_data.low.values[i]# 第1根包含第2根
            case2_1 = temp_data.high.values[-1] < k_data.high.values[i] and temp_data.low.values[-1] > k_data.low.values[i] # 第2根包含第1根
            case2_2 = temp_data.high.values[-1] < k_data.high.values[i] and temp_data.low.values[-1] == k_data.low.values[i] # 第2根包含第1根
            case2_3 = temp_data.high.values[-1] == k_data.high.values[i] and temp_data.low.values[-1] > k_data.low.values[i] # 第2根包含第1根
            case3 = temp_data.high.values[-1] == k_data.high.values[i] and temp_data.low.values[-1] == k_data.low.values[i] # 第1根等于第2根
            case4 = temp_data.high.values[-1] > k_data.high.values[i] and temp_data.low.values[-1] > k_data.low.values[i] # 向下趋势
            case5 = temp_data.high.values[-1] < k_data.high.values[i] and temp_data.low.values[-1] < k_data.low.values[i] # 向上趋势
            if case1_1 or case1_2 or case1_3:
                if zoushi[-1] == 4:
                    temp_data.high.values[-1] = k_data.high.values[i]
                else:
                    temp_data.low.values[-1] = k_data.low.values[i]

            elif case2_1 or case2_2 or case2_3:
                temp_temp = temp_data[-1:]
                temp_data = k_data[i:i+1]
                if zoushi[-1] == 4:
                    temp_data.high.values[-1] = temp_temp.high.values[0]
                else:
                    temp_data.low.values[-1] = temp_temp.low.values[0]

            elif case3:
                zoushi.append(3)
                pass

            elif case4:
                zoushi.append(4)
                after_fenxing = pd.concat([after_fenxing,temp_data],axis = 0)
                temp_data = k_data[i:i+1]

            elif case5:
                zoushi.append(5)
                after_fenxing = pd.concat([after_fenxing,temp_data],axis = 0)
                temp_data = k_data[i:i+1]
                # after_fenxing.head()

        ## 因为使用candlestick2函数，要求输入open、close、high、low。为了美观，处理k线的最大最小值、开盘收盘价，之后k线不显示影线。
        for i in range(len(after_fenxing)):
            if after_fenxing.open.values[i] > after_fenxing.close.values[i]:
                after_fenxing.open.values[i] = after_fenxing.high.values[i]
                after_fenxing.close.values[i] = after_fenxing.low.values[i]
            else:
                after_fenxing.open.values[i] = after_fenxing.low.values[i]
                after_fenxing.close.values[i] = after_fenxing.high.values[i]

        ## 画出k线图
        stock_middle_num = self.middle_num(after_fenxing)
        fig, ax = plt.subplots(figsize = (50,20))
        fig.subplots_adjust(bottom=0.2)
        mpf.candlestick2_ochl(ax, list(after_fenxing.open),list(after_fenxing.close),list(after_fenxing.high),list(after_fenxing.low), width=0.6, colorup='r', colordown='b',alpha=0.75 )
        plt.grid(True)
        dates = after_fenxing.index
        ax.set_xticklabels(dates) # Label x-axis with dates
        # ax.autoscale_view()
        ax.plot(stock_middle_num,'k', lw=1)
        ax.plot(stock_middle_num,'ko')
        plt.setp(plt.gca().get_xticklabels(), rotation=30)
        plt.title(self.coin_type+"_"+self.time_type+time.strftime('%Y-%m-%d-%H-%M-%S')+"_ftb.png")
        self.K_Line_fig=fig
        temp_data=list(map(self.as_num,k_data.close.values))
        return after_fenxing

    def find_top_bottom(self,after_fenxing,time_list):
            ## 找出顶和底
        temp_num = 0 #上一个顶或底的位置
        temp_high = 0 #上一个顶的high值
        temp_low = 0 #上一个底的low值
        temp_type = 0 # 上一个记录位置的类型
        i = 1
        fenxing_type = [] # 记录分型点的类型，1为顶分型，-1为底分型
        fenxing_time = [] # 记录分型点的时间
        fenxing_plot = [] # 记录点的数值，为顶分型去high值，为底分型去low值
        fenxing_data = pd.DataFrame() # 分型点的DataFrame值
        while (i < len(after_fenxing)-1):
            case1 = after_fenxing.high.values[i-1]<after_fenxing.high.values[i] and after_fenxing.high.values[i]>after_fenxing.high.values[i+1] #顶分型
            case2 = after_fenxing.low.values[i-1]>after_fenxing.low.values[i] and after_fenxing.low.values[i]<after_fenxing.low.values[i+1] #底分型
            if case1:
                if temp_type == 1: # 如果上一个分型为顶分型，则进行比较，选取高点更高的分型
                    if after_fenxing.high.values[i] <= temp_high:
                        i += 1
                    #                 continue
                    else:
                        temp_high = after_fenxing.high.values[i]
                        temp_num = i
                        temp_type = 1
                        i += 4
                elif temp_type == 2: # 如果上一个分型为底分型，则记录上一个分型，用当前分型与后面的分型比较，选取同向更极端的分型
                    if temp_low >= after_fenxing.high.values[i]: # 如果上一个底分型的底比当前顶分型的顶高，则跳过当前顶分型。
                        i += 1
                    else:
                        fenxing_type.append(-1)
                        fenxing_time.append(time_list[temp_num])
                        fenxing_data = pd.concat([fenxing_data,after_fenxing[temp_num:temp_num+1]],axis = 0)
                        fenxing_plot.append(after_fenxing.high.values[i])
                        temp_high = after_fenxing.high.values[i]
                        temp_num = i
                        temp_type = 1
                        i += 4
                else:
                    temp_high = after_fenxing.high.values[i]
                    temp_num = i
                    temp_type = 1
                    i += 4

            elif case2:
                if temp_type == 2: # 如果上一个分型为底分型，则进行比较，选取低点更低的分型
                    if after_fenxing.low.values[i] >= temp_low:
                        i += 1
                    #                 continue
                    else:
                        temp_low = after_fenxing.low.values[i]
                        temp_num = i
                        temp_type = 2
                        i += 4
                elif temp_type == 1: # 如果上一个分型为顶分型，则记录上一个分型，用当前分型与后面的分型比较，选取同向更极端的分型
                    if temp_high <= after_fenxing.low.values[i]: # 如果上一个顶分型的底比当前底分型的底低，则跳过当前底分型。
                        i += 1
                    else:
                        fenxing_type.append(1)
                        fenxing_time.append(time_list[temp_num])
                        fenxing_data = pd.concat([fenxing_data,after_fenxing[temp_num:temp_num+1]],axis = 0)
                        fenxing_plot.append(after_fenxing.low.values[i])
                        temp_low = after_fenxing.low.values[i]
                        temp_num = i
                        temp_type = 2
                        i += 4
                else:
                    temp_low = after_fenxing.low.values[i]
                    temp_num = i
                    temp_type = 2
                    i += 4

            else:
                i += 1


        fig, ax = plt.subplots(figsize = (20,5))
        ax.set_xticklabels(after_fenxing.index) # Label x-axis with dates
        ax.autoscale_view()
        ax.plot(fenxing_plot,'k', lw=1)
        ax.plot(fenxing_plot,'o')
        ax.grid(True)
        plt.setp(plt.gca().get_xticklabels(), rotation=30)
        plt.title(self.coin_type+"_"+self.time_type+time.strftime('%Y-%m-%d-%H-%M-%S')+"_ftb.png")
        self.zhibiao_fig=fig
        return fenxing_data,fenxing_plot,fenxing_type
