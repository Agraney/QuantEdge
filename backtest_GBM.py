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

# Simulation to predict multiple different paths 
from GBM_monte import generate_multiple_gbm_paths, save_all_gbm_paths_plot

def calculate_cagr(df):
    start_value = df['Portfolio Value'].iloc[0]
    end_value = df['Portfolio Value'].iloc[-1]
    start_date = df['Date'].iloc[0]
    end_date = df['Date'].iloc[-1]
    days = (end_date - start_date).days
    return ((end_value / start_value) ** (365.0 / days)) - 1 if days > 0 else 0

def calculate_sharpe(df):
    returns = df['Portfolio Value'].pct_change().dropna()
    return (returns.mean() / returns.std()) * np.sqrt(252) if not returns.empty else 0

def calculate_max_drawdown(df):
    rolling_max = df['Portfolio Value'].cummax()
    drawdown = df['Portfolio Value'] / rolling_max - 1.0
    return drawdown.min()

class MACDRSI_RiskStrategy(bt.Strategy):
    params = dict(
        risk_percent=0.03,
        stop_loss_pct=0.05,
        take_profit_pct=0.1,
        path_id=0,
        output_trade_csv='trades_path.csv'
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

        # Create trade CSV with header
        with open(self.p.output_trade_csv, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Path ID', 'Entry Date', 'Entry Price', 'Exit Date', 'Exit Price',
                'Stop Loss', 'Take Profit', 'Size', 'P&L', 'Net P&L', 'Result', 'Capital At Entry'
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
                    self.entry_date = self.data.datetime.date(0)
                    self.buy(size=size)
        else:
            if price <= self.stop_loss or price >= self.take_profit:
                self.exit_date = self.data.datetime.date(0)
                self.exit_price = price
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
            if pnl > 0:
                self.win_count += 1
            else:
                self.loss_count += 1
            # Write trade to CSV
            with open(self.p.output_trade_csv, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    self.p.path_id,
                    self.entry_date, f"{self.entry_price:.2f}",
                    self.exit_date, f"{self.exit_price:.2f}",
                    f"{self.stop_loss:.2f}", f"{self.take_profit:.2f}",
                    self.entry_size, f"{pnl:.2f}", f"{net_pnl:.2f}",
                    result, f"{self.entry_cash:.2f}"
                ])

    def stop(self):
        self.results = {
            'Total Trades': self.trade_count,
            'Wins': self.win_count,
            'Losses': self.loss_count,
            'Win Rate': 100 * self.win_count / self.trade_count if self.trade_count else 0,
            'Daily Values': self.daily_values
        }

def run_backtest_on_gbm_path(df, path_id, summary_csv):
    df['OpenInterest'] = 0
    df.index = pd.to_datetime(df.index)
    feed = bt.feeds.PandasData(dataname=df)

    cerebro = bt.Cerebro()
    output_trade_csv = f"trades_path_{path_id}.csv"
    cerebro.addstrategy(MACDRSI_RiskStrategy, path_id=path_id, output_trade_csv=output_trade_csv)
    cerebro.adddata(feed)
    cerebro.broker.setcash(100000)
    strategies = cerebro.run()
    strat = strategies[0]

    perf_df = pd.DataFrame(strat.daily_values)
    perf_df.drop_duplicates(subset='Date', inplace=True)
    perf_df['Date'] = pd.to_datetime(perf_df['Date'])

    final_value = cerebro.broker.getvalue()
    cagr = calculate_cagr(perf_df)
    sharpe = calculate_sharpe(perf_df)
    max_dd = calculate_max_drawdown(perf_df)

    with open(summary_csv, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            path_id, perf_df['Portfolio Value'].iloc[0], final_value,
            f"{cagr:.4f}", f"{sharpe:.2f}", f"{max_dd:.4f}",
            strat.results['Total Trades'], strat.results['Win Rate']
        ])

if __name__ == '__main__':
    n_paths = 10
    paths = generate_multiple_gbm_paths(n_paths=n_paths, S0=1000, mu=0.12, sigma=0.25, days=252)
    save_all_gbm_paths_plot(paths, filename="simulated_paths_run1.png")

    summary_csv = "gbm_backtest_summary.csv"
    if not os.path.exists(summary_csv):
        with open(summary_csv, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Path ID', 'Initial Value', 'Final Value',
                'CAGR', 'Sharpe Ratio', 'Max Drawdown',
                'Total Trades', 'Win Rate (%)'
            ])

    for i, df in enumerate(paths):
        print(f"\nRunning backtest for path {i+1}...")
        run_backtest_on_gbm_path(df.copy(), i+1, summary_csv)

    print("\n✅ All GBM backtests completed and results saved to gbm_backtest_summary.csv")
