#!/usr/bin/python
#coding:utf-8
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from market_strategy import config
from market_strategy.Order import Order


class MyDBSession:
    def __init__(self):
        pass

    #   将函数参数转换为字典
    def str_format(self,**args):
        tmpl = 'mysql+mysqlconnector://{username}:{password}@{ip}:3306/{db_name}'
        #  将字典转换为函数参数格式
        return tmpl.format(**args)

    def create_engine(self,link):
        engine = create_engine(link)
        return engine

    def getDBSessionClass(self,db_map):
        link=self.str_format(**db_map)
        engine=self.create_engine(link)
        DBSessionClass = sessionmaker(bind=engine)
        return DBSessionClass


# dbSession=MyDBSession()
#
# db_map={"username":config.username,"password":config.password,"ip":config.ip,"db_name":config.db}
# DBSessionClass=dbSession.getDBSessionClass(db_map)
#
# new_order = Order (ask_order_id="dadas",type=0,buy_price=0.888877,
#                    status=1,start_date="2017-08-09 13:11:14",update_date="2017-08-09 13:11:14",
#                    end_date="2017-08-09 13:11:14",amount=111,coin_type="aeee" )
# # # 添加到session:
# session = DBSessionClass()
# session.add(new_order)

# # 提交即保存到数据库:
# session.commit()
# # 关闭session:
# session.close()