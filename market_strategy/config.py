#!/usr/bin/python
#coding:utf-8

# markets_bak = [
# "BitfinexUSD",
# "BitstampUSD",
# "BTCCCNY",
# "BtceEUR",
# "BtceUSD",
# "CampBXUSD",
# "CoinbaseUSD",
# "GeminiUSD",
# "KrakenEUR",
# "KrakenUSD",
# "OKCoinCNY",
# "PaymiumEUR",
# ]

markets = [
    "BinanceETH",
    "GateETH",
]
# markets = [
#     "BinanceAEUSDT",
#     "GateAEUSDT",
# ]
#

# observers if any
# ["Logger", "DetailedLogger", "TraderBot", "TraderBotSim", "HistoryDumper", "Emailer"]
observers = ["Logger"]

market_expiration_time = 120  # in seconds: 2 minutes

refresh_rate = 50


#### Trader Bot Config
# Access to Private APIs

paymium_username = "FIXME"
paymium_password = "FIXME"
paymium_address = "FIXME"  # to deposit btc from markets / wallets

bitstamp_username = "FIXME"
bitstamp_password = "FIXME"


# SafeGuards
max_tx_volume = 10000  # in AE
min_tx_volume = 200  # in AE
balance_margin = 0.05  # 5%
profit_margin = 0.003  # 5%
base_margin_perc = 0.00162 #0.162%
profit_thresh = 1  # in CNY
perc_thresh = 2  # in % 百分比
min_total_volume = 0.01 #最少成交量
min_piece = 10 #最小分量数


# SafeGuards_bak
# max_tx_volume = 10  # in BTC
# min_tx_volume = 1  # in BTC
# balance_margin = 0.05  # 5%
# profit_thresh = 1  # in EUR
# perc_thresh = 2  # in %

#### Emailer Observer Config
smtp_host = 'FIXME'
smtp_login = 'FIXME'
smtp_passwd = 'FIXME'
smtp_from = 'FIXME'
smtp_to = 'FIXME'

#### XMPP Observer
xmpp_jid = "FROM@jabber.org"
xmpp_password = "FIXME"
xmpp_to = "TO@jabber.org"


### mysql

username="root"
password="5601564aA"
ip="47.94.199.58"
db="market_strategy"
db_game="market_strategy_game"

###
broker_num =  1
threadpool_5m_worker = 10
threadpool_15m_worker = 5
threadpool_30m_worker = 3


### 实体操作开关（market_game_start = 0 （0：关闭 1：开启））
market_game_start = False

### 买入点，点位，不能超过的点位
average_line_buy = 1

average_line_sell = 2

close_rate = 0.006

###
#平均线双重底
DoubleBottomAverage = 1
#平均线策略
AverageStrategy = 2
#MA均线策略
MaCrossAverage = 3
#海龟策略
TurtleAverage = 4
#双金叉策略
DoubleBottomMACD =5
#维克多123-分型策略
VectorType = 6
#average背驰
DivergenceAverage=7
#average背驰——ma90up
DivergenceAverageMA90Up=8
#average_ma90up
AverageMa90up=9
#BottomUpAverage 底分型up，ma3拉升有力
BottomUpAverage=10
#BottomUpAverage 底分型up，ma3拉升有力
BreakthroughHighPointAverage=11
#山行
MountainAverage=12

#eth_left_size
eth_left_size=2


#binnace
binance_key='kuwmKbN8WnHhjgqewo82rND4Z4hSuUyVfSybOcuHw2gROvKDlt4D3cRWxyaUrqVT'
binance_secret='XBVoEIosEtKPS25QvvtSwrFLrkW0wrex9BsjVdnihvyUWoIcIsMX0P1TbAS0btRy'

#强制画图
draw_force = False