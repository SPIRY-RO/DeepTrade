#!/usr/bin/python
#coding:utf-8
import re
import time

from funcat import LLV, HHV, EMA, REF, MA, CROSS
from funcat.time_series import NumericSeries
import pandas as pd
from  market_strategy import config
from market_strategy.market_pair.basePair import BasePair
from market_strategy.myLogger import log as logger
import numpy as np
from concurrent.futures import ThreadPoolExecutor, wait
from market_strategy.Order import Order,DBSession

class turtleAveragePair(BasePair):
    def __init__(self, coin_type, time_type,binance,stop_loss=-0.02):
        self.coin_type = coin_type
        self.time_type = time_type
        self.threadpool = ThreadPoolExecutor(max_workers=1)
        self.strategy_type = config.TurtleAverage
        self.stop_loss = stop_loss
        self.binance = binance
        #市场竞价-操作
    def __market_broker(self,buy_flag, amount, coin_type,rate_close,rate_average,average_line):
        if(buy_flag):
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
            self.buy(bidPrice,coin_type,rate_close,rate_average,average_line,amount=amount)
        else:
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

            self.sell(askPrice,average_line,amount=amount,coin_type=coin_type)

    def get_opportunity_turtleAverage(self,data):
        #不顾一切
        average_data,my_close_list,close_mean_value,ma60,my_open_list=self.get_average_line(data);
        bool_data,average_line=self.get_bool_average(average_data)

        length=average_line.size
        average_line=average_line[length-30:]

        rate_average=average_line[-1]/average_line[-2]-1
        my_close_list=my_close_list.values
        rate_close=my_close_list[-1]/my_close_list[-2]-1

        #之前的高峰超过3 #ma60处于上升其 #反转
        buy_flag=average_line.max()>3\
             and ma60.series[-1]>ma60.series[-2]\
             and bool_data[-1]>bool_data[-2]\
             and average_line[-1]<1.8

        #趋势反转 #average_line 回到3 # 或者巨亏（当前无法获得 0.08） # 或者 ma60 反转
        sell_flag=bool_data[-1]<bool_data[-2]\
                  and average_line[-1]>3\
                  and ma60.series[-1]<ma60.series[-2]

        #
        if(buy_flag
           ):
            futures = []
            futures.append(self.threadpool.submit(self.__market_broker,buy_flag,
                                                  config.min_tx_volume, self.coin_type,rate_close=rate_close,rate_average=rate_average,average_line=average_line))
        elif(sell_flag):
            futures = []
            futures.append(self.threadpool.submit(self.__market_broker,buy_flag,
                                                  config.min_tx_volume, self.coin_type,rate_close=0,rate_average=0,average_line=0))

    def sell(self, askPirce,average_line,coin_type, amount=config.min_tx_volume):
        #对数据库进行更新操作
        # 创建session对象:
        session = DBSession()
        #查询有没有买单的
        #时间
        update_date=time.strftime('%Y-%m-%d %H:%M:%S')
        order_result = session.query(Order).filter(Order.type == 0).filter(Order.coin_type == coin_type). \
            filter(Order.end_date < update_date).filter(Order.time_type == self.time_type). \
            filter(Order.strategy_type == self.strategy_type)
        count=order_result.count()
        if(count>0):
            #说明有成交的买单，那么就可以进行卖出操作了
            #更新数据库
            order=order_result.one()
            order.sell_price = askPirce
            order.buy_price=float(order.buy_price)
            order.profit_rate = askPirce/order.buy_price -1
            order.sell_fee = (askPirce * amount)*0.001
            order.profit = (float(order.sell_price)-float(order.buy_price))*(float(order.amount))- \
                           (float(order.buy_fee) + float(order.sell_fee))
            order.type = 1
            order.ask_order_id = "test_ask_004"
            # 添加到session:
            message="%s:%s执行下单操作成功，卖价为%.8f,数量为%.2f"%(self.coin_type,self.time_type,askPirce,amount)
            logger.warn(message)


            if(order.profit_rate>-0.08):
                #亏损在8%中间就不要动
                # 关闭session:
                session.close()
                return

            #亏损超过1%，卖出
            # 提交即保存到数据库:
            if(config.market_game_start == 1):
                for pair_map in config.binance_game_coin_pairs:
                    if(pair_map["symbol"] == self.coin_type):
                        #实体竞技
                        try:
                            balance_data_list=self.binance.get_account()["balances"]
                            asset=self.coin_type.replace("BTC","")
                            for value_map in balance_data_list:
                                if(value_map["asset"]==asset):
                                    free=value_map["free"]
                                    free=float(free)
                                    amount=min(free,amount)
                                    break

                            result=self.binance.order_limit_sell(symbol=self.coin_type, quantity=amount, price=askPirce )
                            order.ask_order_id = result["orderId"]
                            message="下单 %s"%(order.ask_order_id)
                            logger.warn(message)
                        except Exception as  e:
                            logger.fatal(e)


            session.commit()
        # 关闭session:
        session.close()


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

    def get_maLiner(self, data):
        X = np.array(data)
        my_close_list=np.array(X[:,4],dtype=np.float)
        my_close_list = pd.Series(my_close_list)
        close_data=np.array(my_close_list)
        close_data = NumericSeries(close_data)

        ma10=MA(close_data,10)
        ma20=MA(close_data,20)
        ma60=MA(close_data,60)

        return ma10,ma20,ma60




