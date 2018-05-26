#!/usr/bin/python
#coding:utf-8
from market_strategy.myLogger import log as logger
from concurrent.futures import ThreadPoolExecutor, wait, thread
from market_strategy.Order import Order,DBSession
from market_strategy.strategy.average_strategy import AverageStrategyCLI
from market_strategy.strategy.double_bottom_strategy import DoubleBottomStrategyCLI
from market_strategy.strategy.ma10_cross_ma20_ma60_strategy import Ma10CrossMa20Ma60StrategyCLI
from market_strategy.strategy.turtle_average_strategy import TurtleAverageStrategyCLI


class StrategyRunCLI:
    def __init__(self):
        self.threadpool_run = ThreadPoolExecutor(max_workers=4)

    def main(self):
        logger.debug("main")
        self.create_bean()

    def create_bean(self):
        doubleBottomStrategyCLI=DoubleBottomStrategyCLI()
        ma10CrossMa20Ma60StrategyCLI=Ma10CrossMa20Ma60StrategyCLI()
        turtleAverageStrategyCLI=TurtleAverageStrategyCLI()

        self.threadpool_5m_run(doubleBottomStrategyCLI)
        self.threadpool_5m_run(ma10CrossMa20Ma60StrategyCLI)
        self.threadpool_5m_run(turtleAverageStrategyCLI)


    def threadpool_5m_run(self,strategy_bean):
        futures = []
        futures.append(self.threadpool_run.submit(self.__thread_run_strategy,strategy_bean))

    def __thread_run_strategy(self,strategy_bean):
        strategy_bean.main()


def main():
    cli = StrategyRunCLI()
    cli.main()

if __name__ == "__main__":
    main()

