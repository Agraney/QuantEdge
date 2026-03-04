# QuantEdge

An algorithmic trading exploration and backtesting environment built using standard Python financial data libraries like `yfinance` and `backtrader`. It simulates investment strategies based on popular technical indicators (MACD, RSI) and evaluates statistical pricing models (Geometric Brownian Motion).

## Included Features

- **Fetching Real Market Data**: Using `yfinance` to fetch structured past stock data for tickers on Yahoo Finance.
- **Backtesting Framework**: Employs `backtrader` to apply logical trading strategies against historical daily data to assess their performance (CAGR, Sharpe Ratio, Max Drawdown).
- **Geometric Brownian Motion (GBM) Monte Carlo Simulation**: Forecasts alternative stock pricing paths using deterministic drift and random volatility, producing thousands of simulated paths.
- **Combined Indicator Strategies**: Features a dual condition strategy combining MACD signal crossovers with RSI oversold indicators, enforcing strict take-profit and stop-loss risk management parameters.

## Project Structure

* `fetch_data.py`: A simple starter script to fetch and print the OHLC daily stock numbers of a given Yahoo! Finance ticker (e.g., TCS.NS). 
* `indicator.py`: Calculates historical MACD and RSI values on fetched data and visualizes them on a `matplotlib` chart, saving the output as `indicators_plot.png`.
* `GBM_monte.py`: Implements a GBM model to synthetically simulate likely paths of stock prices based on starting price, historical return, and volatility. Generates chart visualizations.
* `backtest.py`: Runs a Backtrader `Cerebro` engine over a defined stock (e.g., RELIANCE.NS) utilizing the `MACDRSI_RiskStrategy`. It simulates buying and selling while maintaining a digital portfolio balance and exports all performed trades to a generated `trades.csv` file.
* `backtest_GBM.py`: Performs backtesting over the generated synthetic GBM variations of stock pricing. Very useful for estimating how the `MACDRSI_RiskStrategy` could handle significantly different variations of market conditions. Saves results to `gbm_backtest_summary.csv`.
* `engine/backtester.py`: Contains a generalized execution wrapper of the `backtrader.Cerebro` runner.

## Quickstart

### 1. Requirements

Install all pip requirements by running this line in a terminal with python 3 installed:
```bash
pip install -r requirements.txt
```

### 2. Execution

To visualize indicators over recent RELIANCE.NS stock values:
```bash
python indicator.py
```

To run a single backtest logic over RELIANCE.NS:
```bash
python backtest.py
```

To compute an advanced backtest through multiple simulated GBM pathways:
```bash
python backtest_GBM.py
```
> **Outputs**: This command will produce a series of trade csvs (`trades_path_1.csv`...) documenting trades taken for each path alongside `simulated_paths_run1.png` to view the varied paths taken.
