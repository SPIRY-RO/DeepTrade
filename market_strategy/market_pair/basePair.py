#!/usr/bin/python
#coding:utf-8
import datetime
import os
import re
import time
import traceback

import matplotlib
import pytz
from funcat import LLV, HHV, EMA, REF, MA
from funcat.time_series import NumericSeries
import pandas as pd
from matplotlib.markers import MarkerStyle
from sqlalchemy import or_

from  market_strategy import config
from market_strategy.MyDBSession import MyDBSession
from market_strategy.common.CommonTools import CommonTools
from market_strategy.common.ServerJiao import ServerJiao
from market_strategy.entity.BinanceEntity import BinanceEntity
from market_strategy.myLogger import log as logger
import numpy as np
from concurrent.futures import ThreadPoolExecutor, wait
from market_strategy.Order import Order,DBSession
matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.finance as mpf
from urllib import parse,request

class BasePair:
    def __init__(self, coin_type, time_type,db_config,binance,stop_loss=-0.02):
        self.coin_type = coin_type
        self.time_type = time_type
        self.binance =binance
        self.stop_loss =stop_loss
        self.init_own_config()

    def __del__(self):
        message=self.coin_type+"__del__"
        logger.debug(message)

    def init_own_config(self,username=config.username,password=config.password,ip=config.ip,db_name=config.db):
        self.config={}
        self.zhibiao_axis_map={}
        self.additional_map_list=[]
        self.additional_average_map_list=[]
        self.json_save={}
        self.config["username"]=username
        self.config["password"]=password
        self.config["ip"]=ip
        self.config["db_name"]=db_name
        self.game_flag = False
        self.buy_precondition_satified  = True #满足了，才进入下一笔
        self.sell_precondition_satified = True #满足了，才进入下一笔
        self.check_profit_flag=False

        #市场竞价-操作
    def market_broker(self,buy_flag,sell_flag, amount, coin_type,average_line):
        data=self.binance.get_order_book(symbol=coin_type,limit=5)
        filters=self.binance.get_symbol_info(symbol=coin_type)['filters']
        minPrice=filters[0]['minPrice']
        minQty=filters[1]['minQty']
        market_price=data["bids"][0][0]

        market_price=float(market_price)
        minQty=float(minQty)
        if(minPrice=='0.00000001'):
            market_price=round(float(market_price),8)
        elif(minPrice=='0.00000010'):
            market_price=round(market_price,7)
        elif(minPrice=='0.00000100'):
            market_price=round(market_price,6)
        elif(minPrice=='0.00001000'):
            market_price=round(market_price,5)

        if minQty =='1.00000000':
            amount=amount
        elif minQty =='0.01000000':
            amount=amount+0.02
        elif minQty =='0.00100000':
            amount=amount+0.002


        if(buy_flag):
            logger.debug(self.coin_type+":买入")

            self.buy(market_price,coin_type,average_line,amount=amount)
        elif(sell_flag):
            logger.debug(self.coin_type+":卖出")
            self.sell(market_price,average_line, amount=amount,coin_type=coin_type)
        else:
            logger.debug(self.coin_type+":---------检测利润 卖出")
            self.check_sell(market_price,coin_type=coin_type, amount=amount)

        self.__del__()

    def get_opportunity(self,data):
        #不顾一切
        average_data,my_close_list,mean_value,my_open_list=self.get_average_line(data);
        try :
            bool_data,average_line=self.get_bool_average(average_data)
        except Exception as  e:
            return

        my_close_list=list(my_close_list)

        rate_average=average_line[-1]/average_line[-2]-1
        rate_close=my_close_list[-1]/my_close_list[-2]-1

        buy_flag = np.where(average_line[-1]<config.average_line_buy and bool_data[-1]>bool_data[-2]
                            and mean_value >my_close_list[-1]
                            , True, False)
        sell_flag = np.where( bool_data[-1]<bool_data[-2], True, False)

        buy_flag = buy_flag and (not self.sell_flag ) and (rate_close >= 0 and rate_close<config.close_rate) \
                   and not(self.get_check_average_fake_buy)

        if( buy_flag ):
            logger.debug(self.coin_type+"：买入")
            futures = []
            futures.append(self.threadpool.submit(self.market_broker,buy_flag,sell_flag,
                                                  config.min_tx_volume, self.coin_type,rate_close,rate_average))
        elif(sell_flag ):
            logger.debug(self.coin_type+"：卖出")
            futures = []
            futures.append(self.threadpool.submit(self.market_broker,buy_flag,sell_flag,
                                                  config.min_tx_volume, self.coin_type,rate_close,rate_average))
        else:
            logger.debug(self.coin_type+"：卖出")
            futures = []
            futures.append(self.threadpool.submit(self.market_broker,buy_flag,sell_flag,
                                                  config.min_tx_volume, self.coin_type,rate_close,rate_average))

    def buy(self,bidPrice,coin_type,average_line,amount=config.min_tx_volume):
        order,session=self.save_data_db(bidPrice,amount,coin_type)
        if order is not None  or config.draw_force:
            self.drawPic('buy_flag')
            self.gamePlay(True,bidPrice,amount,order,session)

        session.close()


    def sell(self, askPirce,average_line, coin_type, amount=config.min_tx_volume):
        order,session=self.change_data_db(coin_type,askPirce,amount)
        if order is not None  or config.draw_force:
            self.drawPic('sell_flag')
            self.gamePlay(False,askPirce,amount,order,session)

        session.close()

    def check_sell(self, askPirce, coin_type, amount=config.min_tx_volume):
        self.check_profit_flag = True
        order,session=self.change_data_db(coin_type,askPirce,amount)
        if order is not None  or config.draw_force:
            self.drawPic('sell_flag')
            self.gamePlay(False,askPirce,amount,order,session)

        session.close()

    def save_data_db(self, bidPrice,amount,coin_type):
        #写入数据库
        update_date=time.strftime('%Y-%m-%d %H:%M:%S')
        east8_date = datetime.datetime.fromtimestamp(int(time.time()), pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')

        int_gap_time = self.time_type[:len(self.time_type)-1]
        int_gap_time = int(int_gap_time)
        minute = datetime.datetime.now().minute
        int_gap=int(minute/int_gap_time)
        if((int_gap+1)*int_gap_time<60):
            start_minute = int_gap * int_gap_time
            end_minute = (int_gap+1) * int_gap_time
            time_str="%Y-%m-%d %H:{start_minute:0>2}:00".format(start_minute=start_minute)
            start_date = datetime.datetime.now().strftime(time_str)
            time_str="%Y-%m-%d %H:{end_minute:0>2}:00".format(end_minute=end_minute)
            end_date = datetime.datetime.now().strftime(time_str)
        else:
            start_minute = int_gap * int_gap_time
            time_str="%Y-%m-%d %H:{start_minute:0>2}:00".format(start_minute=start_minute)
            start_date = datetime.datetime.now().strftime(time_str)
            date_time=datetime.datetime.now()+datetime.timedelta(hours=1)
            end_date = date_time.strftime("%Y-%m-%d %H:00:00")

        type = 0
        status=1
        # 创建session对象:
        myDBsession=MyDBSession()
        DBSessionClass=myDBsession.getDBSessionClass(self.config)
        session = DBSessionClass()

        buy_fee=bidPrice*amount*0.001

        order = session.query(Order).filter(or_( Order.type == 0 ,Order.type == 2) ).filter(Order.coin_type == coin_type) \
            .filter(Order.time_type == self.time_type).filter(Order.strategy_type == self.strategy_type)
        count=order.count()

        if(count>0 ):
            #说明里面已经存在过了
            session.close()
            return None,session
        else:
            new_order = Order (type=type,buy_price=bidPrice,
                               status=status,start_date=start_date,update_date=update_date,
                               end_date=end_date,amount=amount,coin_type=coin_type,buy_fee=buy_fee,
                               time_type=self.time_type,east8_date=east8_date
                               ,strategy_type=self.strategy_type,json_save=str(self.json_save))
            # 添加到session:
            session.add(new_order)
            message="%s--%s:%s执行下单操作成功，买价为%.8f,数量为%.2f"%(self.config["db_name"],self.coin_type,self.time_type,bidPrice,amount)
            logger.warn(message)

            # 提交即保存到数据库:3
            if config.market_game_start:
                pass
            else:
                session.commit()

            return new_order,session

    def change_data_db(self,coin_type,askPirce,amount):
        #对数据库进行更新操作
        # 创建session对象:
        myDBsession=MyDBSession()
        DBSessionClass=myDBsession.getDBSessionClass(self.config)
        session = DBSessionClass()
        #查询有没有买单的，或者是等待卖出的
        #时间
        update_date=time.strftime('%Y-%m-%d %H:%M:%S')
        order_result = session.query(Order).filter(or_( Order.type == 0 ,Order.type == 2) ).filter(Order.coin_type == coin_type). \
            filter(Order.end_date < update_date).filter(Order.time_type == self.time_type). \
            filter(Order.strategy_type == self.strategy_type)

        count=order_result.count()
        if(count>0):
            #说明有成交的买单，那么就可以进行卖出操作了
            #更新数据库
            order=order_result.one()
            order.sell_price = askPirce
            order.buy_price=float(order.buy_price)
            order.profit_rate = askPirce/order.buy_price -1-0.002
            order.sell_fee = (askPirce * amount)*0.001
            order.type = 1
            order.profit = (float(order.sell_price)-float(order.buy_price))*(float(order.amount))- \
                           (float(order.buy_fee) + float(order.sell_fee))

            if self.sell_precondition_satified and order.profit_rate<0 and order.profit_rate > self.stop_loss and not(self.check_profit_flag)  :
                message=self.coin_type+" 利润率不行直接返回  , profit:"+CommonTools.as_num(order.profit_rate,8);
                logger.warn(message)
                return None,session

            if(self.check_profit_flag):
                if(order.profit_rate<0.02):
                    message=self.coin_type+" 利润率获利不大直接返回  , profit:"+CommonTools.as_num(order.profit_rate,8);
                    logger.warn(message)
                    return None,session

            # 添加到session:
            message="%s--%s:%s执行下单操作成功，卖价为%.8f,数量为%.2f，利润率为：%s"%(self.config["db_name"],self.coin_type,self.time_type,askPirce,amount,CommonTools.as_num(order.profit_rate,8))
            logger.warn(message)
            if config.market_game_start:
                pass
            else:
                session.commit()

            return order,session
        else:
            session.close()
            return None,session

    def change_data_db(self,coin_type,askPirce,amount):
        #对数据库进行更新操作
        # 创建session对象:
        myDBsession=MyDBSession()
        DBSessionClass=myDBsession.getDBSessionClass(self.config)
        session = DBSessionClass()
        #查询有没有买单的，或者是等待卖出的
        #时间
        update_date=time.strftime('%Y-%m-%d %H:%M:%S')
        order_result = session.query(Order).filter(or_( Order.type == 0 ,Order.type == 2) ).filter(Order.coin_type == coin_type). \
            filter(Order.end_date < update_date).filter(Order.time_type == self.time_type). \
            filter(Order.strategy_type == self.strategy_type)

        count=order_result.count()
        if(count>0):
            #说明有成交的买单，那么就可以进行卖出操作了
            #更新数据库
            order=order_result.one()
            order.sell_price = askPirce
            order.buy_price=float(order.buy_price)
            order.profit_rate = askPirce/order.buy_price -1-0.002
            order.sell_fee = (askPirce * amount)*0.002
            order.type = 1
            order.profit = (float(order.sell_price)-float(order.buy_price))*(float(order.amount))- \
                           (float(order.buy_fee) + float(order.sell_fee))

            if self.sell_precondition_satified and order.profit_rate<0 and order.profit_rate > self.stop_loss   :
                message=self.coin_type+" 利润率不行直接返回  , profit:"+CommonTools.as_num(order.profit_rate,8);
                logger.warn(message)
                return None,session


            # 添加到session:
            message="%s--%s:%s执行下单操作成功，卖价为%.8f,数量为%.2f，利润率为：%s"%(self.config["db_name"],self.coin_type,self.time_type,askPirce,amount,CommonTools.as_num(order.profit_rate,8))
            logger.warn(message)
            if config.market_game_start:
                pass
            else:
                session.commit()

            return order,session
        else:
            session.close()
            return None,session


    def draw_k_line(self, path,title):
        X=self.X
        data={}
        data["open"]=np.array(X[:, 1], dtype=np.float)[-500:]
        data["close"]=np.array(X[:, 4], dtype=np.float)[-500:]
        data["high"]=np.array(X[:, 2], dtype=np.float)[-500:]
        data["low"]=np.array(X[:, 3], dtype=np.float)[-500:]

        self.average_axis_buy["Y"]=data["close"][self.average_axis_buy["X"]]
        self.average_axis_sell["Y"]=data["close"][self.average_axis_sell["X"]]

        fig, ax = plt.subplots(figsize = (50,20))
        fig.subplots_adjust(bottom=0.2)
        plt.grid(True)
        mpf.candlestick2_ochl(ax, data["open"],data["close"],data["high"],data["low"], width=0.6, colorup='r', colordown='green',alpha=0.75 )
        hhv_20=HHV(self.ma3,50)
        hhv_20=hhv_20.series[-500:]

        ax.plot(self.ma90.series[-500:])
        ax.plot(self.ma3.series[-500:],color='#054E9F')
        ax.plot(hhv_20,color='#436EEE')
        axis_map,judge_trend_map=self.get_top_liner_point()

        ax.scatter(axis_map["X"],axis_map["Y"],s=75)
        ax.scatter(judge_trend_map["X"],judge_trend_map["Y"],s=75,c='#FF00FF',marker='x')
        ax.scatter(self.average_axis_buy["X"],self.average_axis_buy["Y"],s=75,c='#FF00FF',marker='D')
        ax.scatter(self.average_axis_sell["X"],self.average_axis_sell["Y"]*1.02 ,s=300, c='green',marker='v')
        if len(self.zhibiao_axis_map)>0:
            ax.scatter(self.zhibiao_axis_map["X"],self.zhibiao_axis_map["Y"]*0.98 ,s=300, c='r',marker="^")

        if len(self.additional_map_list)>0:
            for additional_map in self.additional_map_list:
                for i,txt in enumerate(additional_map["Y"]):
                    ax.annotate(CommonTools.as_num(additional_map["Z"][i],2) ,(additional_map["X"][i],additional_map["Y"][i]))


        plt.setp(plt.gca().get_xticklabels(), rotation=30)
        plt.title(title)
        fig.savefig(path)
        self.X=None

    def draw_zhibiao(self, path, title):
        fig, ax = plt.subplots(figsize = (50,20))
        fig.subplots_adjust(bottom=0.2)
        plt.grid(True)
        ax.plot(self.average_data.series[-500:],"-*")
        plt.setp(plt.gca().get_xticklabels(), rotation=30)

        if len(self.additional_average_map_list)>0:
            for additional_map in self.additional_average_map_list:
                ax.scatter(additional_map["X"],additional_map["Y"],s=75,c=additional_map["C"],marker='D')

        fig.autofmt_xdate()
        plt.title(title)
        fig.savefig(path)

    def gamePlay(self,buy_flag, Price, amount, new_order, session):
        if(config.market_game_start ):
            if config.market_game_start:
                #检测 订单列表 状态
                self.check_order_list()
            #实体竞技
            if buy_flag  :
                try:
                    balance_data_list=self.binance.get_account()["balances"]
                    eth_asset=balance_data_list[2]
                    free = float(eth_asset["free"])
                    locked = float(eth_asset["locked"])

                    if free<config.eth_left_size:
                        return

                    two_str1=str(amount)[-2:]
                    bool_flag=re.match("00", two_str1)
                    if(bool_flag):
                        can_buy_amount=round(0.5/Price,0) #0.5个eth
                    else:
                        can_buy_amount=round(0.5/Price,2) #0.5个eth

                    if(free>0.5 and can_buy_amount>0):
                        result=self.binance.order_limit_buy(symbol=self.coin_type, quantity=can_buy_amount, price=Price )

                        new_order.amount=can_buy_amount
                        new_order.bid_order_id = result["orderId"]
                        message="下单 %s"%(new_order.bid_order_id)
                        logger.warn(message)
                        logger.warn(str(result))
                        session.commit()

                        message=str(result)
                        logger.warn(message)
                        ServerJiao.send_server_warn(message)
                    else:
                        logger.warn(self.coin_type+"金额不足")
                except Exception as  e:
                    traceback.print_exc()
                    message=self.coin_type+":"+str(e)
                    logger.fatal(message)
                    ServerJiao.send_server_warn(message)
            else:
            # 提交即保存到数据库:
                try:
                    balance_data_list=self.binance.get_account()["balances"]
                    eth_asset=balance_data_list[2]
                    eth_free = float(eth_asset["free"])
                    eth_locked = float(eth_asset["locked"])
                    asset=self.coin_type.replace("ETH","")
                    for value_map in balance_data_list:
                        if(value_map["asset"]==asset):
                            free=value_map["free"]
                            locked=value_map["locked"]
                            free=float(free)
                            locked=float(locked)
                            break

                    two_str1=str(amount)[-2:]
                    bool_flag=re.match("00", two_str1)
                    if(bool_flag):
                        amount= np.math.floor(free) #0.5个eth
                    else:
                        free=free*100
                        free= np.math.floor(free) #0.5个eth
                        amount=free/100

                    if(amount>0 and amount*Price>0.01) :
                        result=self.binance.order_limit_sell(symbol=self.coin_type, quantity=amount, price=Price )

                        new_order.ask_order_id = result["orderId"]
                        message=self.coin_type+":下单 %s"%(new_order.ask_order_id)
                        logger.warn(message)
                        logger.warn(str(result))
                        new_order.amount=amount
                        new_order.type= 1
                        session.commit()

                        message=self.coin_type+"___下单卖出____"+str(result)
                        logger.warn(message)
                        ServerJiao.send_server_warn(message)

                        #根据eth lock  数量 取消买单
                        if eth_locked>0:
                            cancel_result=self.binance.cancel_order(symbol=new_order.coin_type,orderId=new_order.bid_order_id)
                            message=self.coin_type+"___取消下单____"+str(cancel_result)
                            logger.warn(message)
                            ServerJiao.send_server_warn(message)
                        else:
                            message="eth 没有 lock 记录"
                            ServerJiao.send_server_warn(message)
                    else:
                        new_order.type= 4
                        session.commit()
                        logger.warn(self.coin_type+":没有足够数量")
                except Exception as  e:
                    traceback.print_exc()
                    message=self.coin_type+":"+str(e)
                    logger.fatal(message)
                    ServerJiao.send_server_warn(message)


    def get_check_average_fake_buy(self):
        average_list=self.average_data.series
        average_fake_buy_flag=average_list[-1]>average_list[-2] and average_list[-2]<average_list[-3]  \
                              and average_list[-3] >average_list[-4]

        return average_fake_buy_flag


    def get_average_line(self,data):
        X = np.array(data)
        self.X=X
        my_low_list= np.array(X[:,3],dtype=np.float)
        my_low_list = pd.Series(my_low_list)
        llv_data = NumericSeries(my_low_list)
        llv_data=LLV(llv_data,200)
        ret = list(map(float, X[:,2]))
        my_high_list=list(ret)
        my_high_list = pd.Series(my_high_list)
        hhv_data = NumericSeries(my_high_list)
        hhv_data = HHV(hhv_data,200)

        my_close_list=np.array(X[:,4],dtype=np.float)
        my_close_list = pd.Series(my_close_list)
        close_data=np.array(my_close_list)
        close_data = NumericSeries(close_data)

        my_open_list=np.array(X[:,1],dtype=np.float)

        fluctuation_line = EMA((close_data-llv_data)/(hhv_data-llv_data)*4,4)

        ret = list(map(float, X[:,6]))
        time_data = list(ret)
        #信息:=平均线>=REF(平均线,1);
        average_data = EMA (fluctuation_line,3)

        my_open_list=my_open_list[-500:]
        my_close_list=my_close_list[-500:]
        close_mean_value=  my_close_list.mean()

        self.ma90=MA(close_data,90)
        self.ma3=MA(close_data,3)

        return average_data,my_close_list,close_mean_value,my_open_list

    def get_bool_average(self,average_data):
        self.average_data=average_data
        length=len(average_data)

        ref_al=REF(average_data,1).series[length-500-1:]
        ref_al_2=REF(average_data,2).series[length-500-2:]
        average_line=average_data.series[length-500:]
        if(len(average_line)!=len(ref_al)):
            return None,None

        ref_bool_data_position_2 = np.where(ref_al< ref_al_2)
        ref_bool_data_position = np.where(ref_al<average_line)
        intersect1d_list=np.intersect1d(ref_bool_data_position_2,ref_bool_data_position)
        self.average_axis_buy={}
        temp1=np.where(average_line<0.5)[-1]
        self.average_axis_buy["X"]=np.intersect1d(intersect1d_list,temp1) # 买点 小于 0.5
        self.average_axis_buy["Z"]=average_line[self.average_axis_buy["X"]]
        self.average_axis_sell={}
        self.average_axis_sell["X"]=np.where(average_line<ref_al)[-1]

        ref_data=average_line-ref_al
        ref_bool_data = ref_data >0 if True else False

        average_map={}
        average_map["X"]=self.average_axis_buy["X"]
        average_map["Y"]=self.average_axis_buy["Z"]
        average_map["C"]="#DC143C"
        self.additional_average_map_list.append(average_map)

        return ref_bool_data,average_line

    # 市场竞价-操作
    def get_history_data(self):
        try:
            data=self.binance.get_klines(symbol=self.coin_type,interval=self.time_type)
        except Exception as e :
            traceback.print_exc()
            message=self.coin_type+": fall down"
            logger.fatal(message)
            data=self.get_history_data()

        return data

    def get_top_liner_point(self):
        axis_map={}

        my_close_list=np.array(self.X[:,4],dtype=np.float)

        my_close_list=my_close_list[-500:]
        top_value_list=my_close_list[self.top_flag_position_list]

        length=len(top_value_list)
        select_x=[]
        select_y=[]

        for index in range(length):
            if index-1>0:
                left=top_value_list[index-1]
                value=top_value_list[index]

        axis_map["X"]=self.top_flag_position_list
        axis_map["Y"]=top_value_list
        #趋势判断
        judge_trend_map=self.judeg_trend(axis_map)
        return axis_map,judge_trend_map

    def get_top_flag_position_list(self):
        abs_close_list=self.abs_close_list()
        close_series = NumericSeries(abs_close_list)
        ref_close_2=REF(close_series,2)
        ref_close_1=REF(close_series,1)

        list1=np.where(ref_close_1.series[-500:]>ref_close_2.series[-500:])
        list2=np.where(ref_close_1.series[-500:]>close_series.series[-500:])

        intersect1d_list=np.intersect1d(list1, list2)
        self.top_flag_position_list=intersect1d_list

    def abs_close_list(self):
        my_close_list=np.array(self.X[:,4],dtype=np.float)
        my_open_list=np.array(self.X[:,1],dtype=np.float)
        list_result = list(map(lambda close,open : close if(close>open) else open ,my_close_list, my_open_list))
        list_result=np.array(list_result)
        return list_result


    def check_order_list(self):
        result=self.binance.get_open_orders()
        for entity in result:
            binance_entity=BinanceEntity(**entity)

            if self.coin_type != binance_entity.symbol:
                continue

            #撤单，
            cancel_result=self.binance.cancel_order(symbol=binance_entity.symbol,orderId=binance_entity.orderId)
            ServerJiao.send_server_warn(cancel_result,text=self.coin_type+':撤单'+binance_entity.side)
            #更新数据库
            myDBsession=MyDBSession()
            DBSessionClass=myDBsession.getDBSessionClass(self.config)
            session = DBSessionClass()
            if(binance_entity.side=='SELL'):
                order_result = session.query(Order).filter(Order.ask_order_id == binance_entity.orderId)
                count=order_result.count()
                if(count>0):
                    order=order_result.one()
                    order.type=2
                    order.achieve_amount=binance_entity.executedQty
                    session.commit()
            elif(binance_entity.side=='BUY'):
                order_result = session.query(Order).filter(Order.bid_order_id == binance_entity.orderId)
                count=order_result.count()
                if(count>0 and binance_entity.executedQty==0):
                    order=order_result.one()
                    order.type=3
                    session.commit()

    def judeg_trend(self, axis_map):
        intersect1d_list=axis_map["X"]
        top_value_list=axis_map["Y"]
        tmp_x=[]
        tmp_y=[]
        judge_trend_map={}
        length=len(top_value_list)
        for index in range(length):
            left=index-1
            right=index+1
            if left<0 or right>length-1:
                continue
            else:
                left_value=top_value_list[left]
                value=top_value_list[index]
                right_value=top_value_list[right]

                if value>left_value and value>right_value:
                    position_value=intersect1d_list[index]
                    if position_value>300:
                        tmp_x.append(intersect1d_list[index])
                        tmp_y.append(top_value_list[index])

        if len(tmp_x)>0:
            max_value=max(tmp_y)
            if tmp_y[-1]==max_value:
                #当前是最高点，产生上涨趋势线
                pass
            else:
                #当前非最高点，必然产生下跌趋势线、
                pass

        judge_trend_map["X"]=tmp_x
        judge_trend_map["Y"]=tmp_y
        return judge_trend_map

    def drawPic(self,type_str):
        if self.strategy_type == config.VectorType:
            #draw_k_line
            dir_path="log/"+self.config["db_name"]+"_"+self.coin_type+"_"+self.time_type+time.strftime('%Y-%m-%d-%H-%M-%S')+"/"
            os.mkdir(dir_path)
            path=dir_path+type_str+"_draw_k_line.png"
            title=self.coin_type+"_"+self.time_type+time.strftime('%Y-%m-%d-%H-%M-%S')+"buy_flag"+"draw_k_line"
            self.draw_k_line(path,title)

            path=dir_path+type_str+"_K_Line_fig.png"
            self.K_Line_fig.savefig(path)
            self.K_Line_fig.clf()
            path=dir_path+type_str+"_zhibiao_fig.png"
            self.zhibiao_fig.savefig(path)
            self.zhibiao_fig.clf()
        else:
            #draw_k_line
            dir_path="log/"+self.config["db_name"]+"_"+self.coin_type+"_"+self.time_type+time.strftime('%Y-%m-%d-%H-%M-%S')+"/"
            os.mkdir(dir_path)
            path=dir_path+type_str+"_draw_k_line.png"
            title=self.coin_type+"_"+self.time_type+time.strftime('%Y-%m-%d-%H-%M-%S')+type_str+"draw_k_line"
            self.draw_k_line(path,title)
            #draw_zhibiao
            path=dir_path+type_str+"_draw_zhibiao.png"
            title=self.coin_type+"_"+self.time_type+time.strftime('%Y-%m-%d-%H-%M-%S')+type_str+"draw_zhibiao"
            self.draw_zhibiao(path,title)




