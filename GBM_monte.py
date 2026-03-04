import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def save_all_gbm_paths_plot(paths, filename="gbm_simulated_paths.png"):
    plt.figure(figsize=(12, 6))
    for i, df in enumerate(paths):
        plt.plot(df.index, df['Close'], label=f'Path {i+1}', alpha=0.6)
    plt.title('Simulated GBM Stock Price Paths')
    plt.xlabel('Date')
    plt.ylabel('Stock Price (₹)')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()  # Close the plot to free memory

def generate_gbm_prices(S0, mu, sigma, days, dt=1/252):
    """
    Generate GBM stock prices.

    Args:
        S0: Initial stock price
        mu: Expected return (e.g., 0.1 for 10%)
        sigma: Volatility (e.g., 0.2 for 20%)
        days: Number of days to simulate
        dt: Time step (1/252 = daily)

    Returns:
        Pandas Series of simulated prices
    """
    np.random.seed()  # remove for true randomness
    
    #create the time space in years based upon total trading days.
    t = np.linspace(0, days * dt, days)
    
    #W in this is the shock or brownian motion that creates the uncertainty in prices.
    W = np.random.standard_normal(size=days)
    W = np.cumsum(W) * np.sqrt(dt)  
    
    #X is the main log return with 2 components one is the Determinstic drift another is the random volatiliy shock.
    #We subtract sigma square from the deterministic part because of the assumption that random returns compound growth rate will
    # always be smaller (Volatility Drag). It basically discounts for the fact of volatality.
    X = (mu - 0.5 * sigma ** 2) * t + sigma * W
    #We take exp of the log change in the new price.
    S = S0 * np.exp(X)

    dates = pd.bdate_range(start='2020-01-01', periods=days)
    return pd.Series(S, index=dates, name='Close')

def generate_gbm_ohlc(S0, mu, sigma, days):
    close = generate_gbm_prices(S0, mu, sigma, days)
    
    df = pd.DataFrame(index=close.index)
    df['Close'] = close
    df['Open'] = close.shift(1).bfill()
    df['Open'] = close.shift(1).bfill()# assume next day opens at yesterday’s close
    df['High'] = df[['Open', 'Close']].max(axis=1) * (1 + np.random.uniform(0.001, 0.01, size=len(df)))
    df['Low'] = df[['Open', 'Close']].min(axis=1) * (1 - np.random.uniform(0.001, 0.01, size=len(df)))
    df['Volume'] = np.random.randint(100000, 500000, size=len(df))

    df.dropna(inplace=True)
    return df


def generate_multiple_gbm_paths(n_paths=100, S0=1000, mu=0.1, sigma=0.2, days=252):
    paths = []
    for i in range(n_paths):
        df = generate_gbm_ohlc(S0, mu, sigma, days)
        paths.append(df)
    return paths

if __name__ == '__main__':
    paths = generate_multiple_gbm_paths()
    save_all_gbm_paths_plot(paths)

