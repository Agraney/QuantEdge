import backtrader as bt
import pandas as pd

# ** this allows to take in multiple different arguments changes with each new strategy.
def run_backtester(strategy_class, df, initial_cash = 100000, **strategy_params):
    df['OpenInterest']= 0
    # This line basically wraps our df into a backtrader data feed object.
    feed = bt.feeds.PandasData(dataname = df)
    #cerebro is the engine responsible to run our strategy over the given data.
    cerebro = bt.Cerebro()
    cerebro.addstrategy(strategy_class, **strategy_params)
    cerebro.adddata(feed)
    cerebro.broker.setcash(initial_cash)

    strategies = cerebro.run()
    strat = strategies[0]
    
    #returns the final value of the portfolio considering the starting price to be 1lakh
    return cerebro.broker.getvalue()
    
    