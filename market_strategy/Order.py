#!/usr/bin/python
#coding:utf-8
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String,Float,DECIMAL,DateTime
import market_strategy.config as config
# 创建对象的基类:
Base = declarative_base()
# 定义Order对象:
class Order(Base):
    # 表的名字:
    __tablename__ = 'order'

    # 表的结构:
    id = Column(Integer, primary_key=True)
    bid_order_id = Column(String(45))
    ask_order_id = Column(String(45))
    type = Column(Integer)
    buy_price = Column(Float(20,10))
    sell_price = Column(Float(20,10))
    status = Column(Integer)
    start_date = Column(DateTime())
    end_date =  Column(DateTime())
    update_date =  Column(DateTime())
    east8_date =  Column(DateTime())
    amount = Column(Float(10,2))
    profit_rate = Column(Float(120,10))
    profit = Column(Float(10,2))
    achieve_amount = Column(Float(20,10))
    coin_type = Column(String(45))
    time_type = Column(String(11))
    buy_fee = Column(Float(20,10))
    sell_fee = Column(Float(20,10))
    close_rate = Column(Float(20,10))
    average_rate = Column(Float(20,10))
    strategy_type = Column(Integer)
    average1 = Column(Float(20,10))
    average2 = Column(Float(20,10))
    ma60_1 = Column(Float(20,10))
    ma60_2 = Column(Float(20,10))
    json_save = Column(String)

#   将函数参数转换为字典
def str_format(**args):
    tmpl = 'mysql+mysqlconnector://{username}:{password}@{ip}:3306/{db}'
    #  将字典转换为函数参数格式
    return tmpl.format(**args)

# 初始化数据库连接:

db_map={"username":config.username,"password":config.password,"ip":config.ip,"db":config.db}
link=str_format(**db_map)
engine = create_engine(link)

# 创建DBSession类型:
DBSession = sessionmaker(bind=engine)


# new_order = Order (ask_order_id="dadas",type=0,buy_price=0.888877,
#                    status=1,start_date="2017-08-09 13:11:14",update_date="2017-08-09 13:11:14",
#                    end_date="2017-08-09 13:11:14",amount=111,coin_type="aeee",ma60_1=round("0.5555",2),ma60_2=round("0.5555",2) )
# # 添加到session:
# session = DBSession()
# session.add(new_order)
# #
# # 提交即保存到数据库:
# session.commit()
# # 关闭session:
# session.close()

