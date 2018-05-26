#coding=utf-8
import itchat
from itchat.content import *

from market_strategy.strategy.base_strategy import StrategyCLI


class ItchatRobot:
    def __init__(self):
        pass

    def main(self):
        self.run_robot()

    def run_robot(self):
        itchat.cli = StrategyCLI()
        itchat.cli.base_init()
        itchat.cli.sell_all()
        itchat.auto_login(hotReload=True,enableCmdQR=2)
        itchat.run()

    @itchat.msg_register(TEXT)
    def simple_reply(msg):
        if msg['Type'] == TEXT and msg["Text"].find('warn.')>-1  :
            ReplyContent = 'I received message: '+msg['Content']
            itchat.send(ReplyContent, toUserName='filehelper')
            command=msg["Text"][5:]
            if command.find("SELLALL")>0:
                itchat.send("执行完毕", toUserName='filehelper')

            itchat.send(ReplyContent, toUserName='filehelper')



def main():
    cli = ItchatRobot()
    cli.main()

if __name__ == "__main__":
    main()
