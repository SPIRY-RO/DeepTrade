
class BinanceEntity:
    #初始化
    def __init__(self,symbol,orderId,clientOrderId,price,origQty,executedQty,status,timeInForce,type,side,stopPrice
                 ,icebergQty,time,isWorking):
        self.symbol=symbol
        self.orderId=orderId
        self.clientOrderId=clientOrderId
        self.price=price
        self.origQty=origQty
        self.executedQty=executedQty
        self.status=status
        self.timeInForce=timeInForce
        self.type=type
        self.side=side
        self.stopPrice=stopPrice
        self.icebergQty=icebergQty
        self.time=time
        self.isWorking=isWorking