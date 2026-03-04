import yfinance as yf
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
from datetime import datetime
import matplotlib.pyplot as plt
import backtrader as bt
import csv
import os
import numpy as np

#Metric to check the 
def calculate_cagr(df):
    start_value = df['Portfolio Value'].iloc[0]
    end_value = df['Portfolio Value'].iloc[-1]
    start_date = df['Date'].iloc[0]
    end_date = df['Date'].iloc[-1]
    
    days = (end_date - start_date).days
    cagr = ((end_value / start_value) ** (365.0 / days)) - 1
    return cagr

def calculate_sharpe(df):
    returns = df['Portfolio Value'].pct_change().dropna()
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
    return sharpe

def calculate_max_drawdown(df):
    rolling_max = df['Portfolio Value'].cummax()
    drawdown = df['Portfolio Value'] / rolling_max - 1.0
    max_drawdown = drawdown.min()
    return max_drawdown

# Step 1: Strategy
class MACDRSI_RiskStrategy(bt.Strategy):
    params = dict(
        risk_percent=0.03,
        stop_loss_pct=0.05,
        take_profit_pct=0.1,
    )

    def __init__(self):
        self.macd = bt.ind.MACD(self.data.close)
        self.signal = self.macd.signal
        self.rsi = bt.ind.RSI(self.data.close, period=14)

        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        self.entry_cash = None
        self.entry_size = None

        self.trade_count = 0
        self.win_count = 0
        self.loss_count = 0
        
        self.daily_values = []

        self.csv_path = 'trades.csv'

        # Create CSV with header if it doesn't exist
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Date', 'Entry Price', 'Exit Price', 'Stop Loss', 'Take Profit',
                    'Size', 'P&L', 'Net P&L', 'Result', 'Capital At Entry'
                ])

    def next(self):
        price = self.data.close[0]

        if not self.position:
            if self.macd.macd[0] > self.signal[0] and self.rsi[0] < 70:
                self.entry_price = price
                self.stop_loss = price * (1 - self.p.stop_loss_pct)
                self.take_profit = price * (1 + self.p.take_profit_pct)

                cash = self.broker.getcash()
                risk_amount = cash * self.p.risk_percent
                risk_per_share = price - self.stop_loss

                if risk_per_share <= 0:
                    return

                size = int(risk_amount / risk_per_share)

                if size > 0:
                    self.entry_cash = cash
                    self.entry_size = size

                    print(f"\n🔔 Trade Signal on {self.data.datetime.date(0)}")
                    print(f"  Capital         : ₹{cash:,.2f}")
                    print(f"  Entry Price     : ₹{price:.2f}")
                    print(f"  Stop Loss       : ₹{self.stop_loss:.2f}")
                    print(f"  Take Profit     : ₹{self.take_profit:.2f}")
                    print(f"  Position Size   : {size} shares")

                    self.buy(size=size)

        else:
            if price <= self.stop_loss or price >= self.take_profit:
                self.close()
        
        self.daily_values.append({
            'Date': self.data.datetime.date(0),
            'Portfolio Value': self.broker.getvalue()
        })


    def notify_trade(self, trade):
        if trade.isclosed:
            self.trade_count += 1
            pnl = trade.pnl
            net_pnl = trade.pnlcomm
            result = 'Win' if pnl > 0 else 'Loss'
            date = self.data.datetime.date(0)
            exit_price = self.data.close[0]

            print(f"\n📈 Trade Closed on {self.data.datetime.date(0)}")
            print(f"  Entry Price : ₹{trade.price:.2f}")             # confirmed entry
            print(f"  Exit Price  : ₹{self.data.close[0]:.2f}")   # confirmed exit
            print(f"  Profit/Loss : ₹{pnl:.2f}")
            print(f"  Net Profit  : ₹{net_pnl:.2f}")

            if pnl > 0:
                self.win_count += 1
            else:
                self.loss_count += 1

            # Save to CSV
            with open(self.csv_path, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    date, f"{trade.price:.2f}", f"{exit_price:.2f}",
                    f"{self.stop_loss:.2f}", f"{self.take_profit:.2f}",
                    self.entry_size, f"{pnl:.2f}", f"{net_pnl:.2f}", result, f"{self.entry_cash:.2f}"
                ])

    def stop(self):
        print("\n===== STRATEGY SUMMARY =====")
        print(f"Total Trades     : {self.trade_count}")
        print(f"Wins             : {self.win_count}")
        print(f"Losses           : {self.loss_count}")
        if self.trade_count > 0:
            print(f"Win Rate         : {100 * self.win_count / self.trade_count:.2f}%")
        print("============================\n")


# Step 2: Load yfinance data
def fetch_data(ticker, start, end):
    # Set auto_adjust=True to get clean adjusted prices
    df = yf.download(ticker, start=start, end=end, auto_adjust=True)

    # If columns are MultiIndex, flatten them
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    # Add OpenInterest if missing
    if 'OpenInterest' not in df.columns:
        df['OpenInterest'] = 0

    df.dropna(inplace=True)
    df.index = pd.to_datetime(df.index)

    print("Cleaned Columns:", df.columns.tolist())
    print(df.head())

    return bt.feeds.PandasData(dataname=df)


# Step 3: Backtest
if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MACDRSI_RiskStrategy)

    data = fetch_data('RELIANCE.NS', '2020-01-01', '2024-12-31')
    cerebro.adddata(data)
    cerebro.broker.setcash(100000)
    # cerebro.addsizer(bt.sizers.FixedSize, stake=1000) It only works when i dont calculate size dynamically using the stop loss and all.

    print(f"Starting Portfolio Value: ₹{cerebro.broker.getvalue():,.2f}")
    strategies=cerebro.run()
    # Create a dataframe to store daily portfolio values
    strat = strategies[0]
    performance_df = pd.DataFrame(strat.daily_values)
    performance_df.drop_duplicates(subset='Date', inplace=True)
    performance_df['Date'] = pd.to_datetime(performance_df['Date'])


    final_value = cerebro.broker.getvalue()
    print(f"Final Portfolio Value: ₹{final_value:,.2f}")
    
    cagr = calculate_cagr(performance_df)
    sharpe = calculate_sharpe(performance_df)
    max_dd = calculate_max_drawdown(performance_df)

    print("\n===== PERFORMANCE METRICS =====")
    print(f"CAGR           : {cagr * 100:.2f}%")
    print(f"Sharpe Ratio   : {sharpe:.2f}")
    print(f"Max Drawdown   : {max_dd * 100:.2f}%")
    print("===============================\n")


    # Save plot to file
    # fig = cerebro.plot(style='candlestick')[0][0]
    # fig.savefig("backtest_result.png")
    # print("✅ Plot saved to backtest_result.png")
