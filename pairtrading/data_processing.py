import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

@st.cache_data(ttl=300) # Cache for 5 minutes for speed
def get_market_data(asset1_ticker, asset2_ticker, spread_formula, days=365, rolling_window=90):
    """
    Fetches and processes market data for a pair of assets.

    Args:
        asset1_ticker (str): The ticker for the first asset.
        asset2_ticker (str): The ticker for the second asset.
        spread_formula (str): The formula to calculate the spread.
        days (int): The number of days of historical data to fetch.
        rolling_window (int): The rolling window for Z-score calculation.

    Returns:
        pd.DataFrame: A DataFrame with market data and Z-score calculations.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    tickers = f"{asset1_ticker} {asset2_ticker}"
    try:
        data = yf.download(tickers, start=start_date, end=end_date, progress=False)['Close']
        if data.empty:
            return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

    # Clean Data
    df = data.copy()
    
    # Rename columns for clarity
    df.rename(columns={asset1_ticker: "asset1", asset2_ticker: "asset2"}, inplace=True)
        
    df = df.dropna()

    if 'asset1' not in df.columns or 'asset2' not in df.columns:
        st.error("The downloaded data does not contain the expected asset columns.")
        return pd.DataFrame()
    
    # Calculate Spread & Z-Score
    df = calculate_z_score(df, spread_formula, window=rolling_window)
    
    return df

def calculate_z_score(df: pd.DataFrame, spread_formula: str, window: int) -> pd.DataFrame:
    """
    Calculates the spread and Z-score for a pair of assets.

    Args:
        df (pd.DataFrame): DataFrame containing asset prices.
        spread_formula (str): The formula to calculate the spread.
        window (int): The rolling window period for mean and standard deviation calculation.

    Returns:
        pd.DataFrame: The DataFrame with 'Spread', 'Mean', 'Std', and 'Z_Score' columns added.
    """
    # This is a security risk, but we accept it for flexibility.
    # The user is providing the formula.
    df['Spread'] = eval(spread_formula, {'asset1': df['asset1'], 'asset2': df['asset2']})
    
    # Rolling Statistics
    df['Mean'] = df['Spread'].rolling(window=window).mean()
    df['Std'] = df['Spread'].rolling(window=window).std()
    df['Z_Score'] = (df['Spread'] - df['Mean']) / df['Std']
    
    return df
