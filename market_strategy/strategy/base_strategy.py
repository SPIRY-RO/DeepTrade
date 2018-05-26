#!/usr/bin/python
#coding:utf-8
import datetime
import gc
import traceback

import numpy
from sqlalchemy import or_

from  market_strategy import config
from market_strategy.MyDBSession import MyDBSession
from market_strategy.common.ServerJiao import ServerJiao
from market_strategy.entity.BinanceEntity import BinanceEntity
from market_strategy.http_server.myServer import flask_app
from market_strategy.market_pair.binancePair import BinancePair
from market_strategy.myLogger import log as logger
import time
from concurrent.futures import ThreadPoolExecutor, wait, thread
from market_strategy.Order import Order,DBSession
from tools.binance.client import Client


class StrategyCLI:
    def __init__(self):
        self.market_pairs = []
        self.market_sell_pairs = []

    def base_init(self):
        self.get_binance()
        self.init_db_config()
        self.game_start=True
        self.threadpool_30m = ThreadPoolExecutor(max_workers=3)
        self.threadpool_flask = ThreadPoolExecutor(max_workers=1)
        self.flask_threadpool_run()

    def get_binance(self):
        try:
            self.binance = Client(config.binance_key,
                                  config.binance_secret)
        except Exception as e:
            self.get_binance()

    def main(self):
        logger.debug("main")
        self.base_init()
        self.create_bean()
        try :
            self.loop()
        except Exception as  e:
            logger.fatal("宕机了。。。。。。。。。")
            traceback.print_exc()
            logger.fatal(e)
            self.loop()

    def create_bean(self):
        all_tickers = self.binance.get_all_tickers()
        sell_tickers=self.get_waiting_sell(self.init_db_config())
        binance_coin_pairs_30m =sell_tickers.append(all_tickers)

        for value_map in binance_coin_pairs_30m:
            symbol=value_map["symbol"]
            if(symbol.find("BTC",2)>0):
                merge_bean = BinancePair(value_map["symbol"],"30m",self.binance )
                self.market_pairs.append(merge_bean)

    def loop(self):
        while(True):
            for market_pair in self.market_pairs:
                if(market_pair.time_type == "5m"):
                    self.threadpool_5m_run(market_pair)
                elif(market_pair.time_type == "15m"):
                    self.threadpool_15m_run(market_pair)
                elif(market_pair.time_type == "30m"):
                    self.threadpool_30m_run(market_pair)

            time.sleep(config.refresh_rate)

    # 为线程定义一个函数
    def start_sell_pairs(self,mod):
        if(mod == 3):
            self.create_waiting_sell_bean()
            for market_pair in self.market_sell_pairs:
                self.sell_threadpool_run(market_pair)
        pass

    def sell_threadpool_run(self,market_pair):
        futures = []
        futures.append(self.sell_threadpool.submit(self.market_get_data,market_pair))

    def flask_threadpool_run(self):
        logger.warn("flask  is running")
        futures = []
        #futures.append(self.threadpool_flask.submit(self.run_flask,flask_app))

    def threadpool_30m_run(self,market_pair):
        futures = []
        futures.append(self.threadpool_30m.submit(self.market_get_data,market_pair))


    def market_get_data(self,market_pair):
        market_pair.get_history_data()

    def get_waiting_sell(self,config):
        # 创建session对象:
        myDBsession=MyDBSession()
        DBSessionClass=myDBsession.getDBSessionClass(config)
        session = DBSessionClass()

        order_result = session.query(Order).filter(  or_( Order.type == 0 ,Order.type == 2) ) \
            .filter(Order.strategy_type == self.strategy_type)

        #说明有成交的买单，那么就可以进行卖出操作了
        #更新数据库
        order_list=order_result.all()
        return order_list

    def init_db_config(self,username=config.username,password=config.password,ip=config.ip,db_name=config.db):
        self.config={}
        self.config["username"]=username
        self.config["password"]=password
        self.config["ip"]=ip
        self.config["db_name"]=db_name
        self.game_flag = False

    def run_flask(self,flask_app):
        return
        flask_app.strategy_bean = self
        #flask_app.run(host='0.0.0.0',port=5000,debug=True)

    def sell_all(self):
        result=self.binance.get_open_orders()
        for entity in result:
            binance_entity=BinanceEntity(**entity)

            #撤单，
            cancel_result=self.binance.cancel_order(symbol=binance_entity.symbol,orderId=binance_entity.orderId)
            ServerJiao.send_server_warn(desp=cancel_result,text=binance_entity.symbol+':撤单'+binance_entity.side)


        balance_data_list=self.binance.get_account()["balances"]

        for entity in balance_data_list:
            symbol=entity["asset"]
            free = float(entity["free"])

            if free <1:
                continue

            symbol=symbol+"ETH"
            try :
                free=numpy.floor(free)
                self.binance.order_market_sell(symbol=symbol,quantity=free)
                ServerJiao.send_server_warn(desp=cancel_result,text=binance_entity.symbol+':卖出'+binance_entity.side)
            except Exception as e:
                continue

        message="指令sell_all执行完毕"
        ServerJiao.send_server_warn(message)
        return message

    def change_eth_left(self,amount):
        config.eth_left_size=amount
        return "change_eth_left successfully : "+config.eth_left_size

    def change_game(self):
        config.market_game_start=not(config.market_game_start)
        return "change_game successfully : "+config.market_game_start

def main():
    cli = StrategyCLI()
    cli.main()

if __name__ == "__main__":
    main()

