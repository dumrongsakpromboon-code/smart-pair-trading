import pandas as pd
import streamlit as st

def get_z_score_advice(z_score: float, threshold_high: float, threshold_low: float, asset1_ticker: str, asset2_ticker: str) -> str:
    """
    Provides trading advice based on the Z-score.

    Args:
        z_score (float): The current Z-score.
        threshold_high (float): The upper Z-score threshold.
        threshold_low (float): The lower Z-score threshold.
        asset1_ticker (str): The ticker for asset 1.
        asset2_ticker (str): The ticker for asset 2.

    Returns:
        str: The advice message.
    """
    if z_score > threshold_high:
        advice_msg = f"🚨 Z-Score > {threshold_high}: Focus buying **{asset1_ticker}** (Sell {asset2_ticker} if needed)"
    elif z_score < threshold_low:
        advice_msg = f"🟢 Z-Score < {threshold_low}: Focus buying **{asset2_ticker}** (Sell {asset1_ticker} if needed)"
    else:
        advice_msg = "⚖️ Market Normal: Rebalance as usual"
    return advice_msg

def calculate_portfolio_values(qty_asset1: float, qty_asset2: float, p_asset1: float, p_asset2: float, cash_dca: float) -> tuple[float, float, float]:
    """
    Calculates the current value of the portfolio.

    Args:
        qty_asset1 (float): The quantity of asset 1 holdings.
        qty_asset2 (float): The quantity of asset 2 holdings.
        p_asset1 (float): The current price of asset 1.
        p_asset2 (float): The current price of asset 2.
        cash_dca (float): The amount of cash available.

    Returns:
        tuple[float, float, float]: A tuple containing the value of asset 1, asset 2, and the total portfolio value.
    """
    val_asset1 = qty_asset1 * p_asset1
    val_asset2 = qty_asset2 * p_asset2
    total_val = val_asset1 + val_asset2 + cash_dca
    return val_asset1, val_asset2, total_val

def calculate_target_values(total_val: float, target_asset1_pct: int, target_asset2_pct: int) -> tuple[float, float]:
    """
    Calculates the target value for each asset based on the target allocation.

    Args:
        total_val (float): The total portfolio value.
        target_asset1_pct (int): The target percentage for asset 1.
        target_asset2_pct (int): The target percentage for asset 2.

    Returns:
        tuple[float, float]: A tuple containing the target value for asset 1 and asset 2.
    """
    tgt_val_asset1 = total_val * (target_asset1_pct / 100)
    tgt_val_asset2 = total_val * (target_asset2_pct / 100)
    return tgt_val_asset1, tgt_val_asset2

def calculate_target_diffs(val_asset1: float, val_asset2: float, tgt_val_asset1: float, tgt_val_asset2: float) -> tuple[float, float]:
    """
    Calculates the difference between the target and current values.
    """
    diff_asset1 = tgt_val_asset1 - val_asset1
    diff_asset2 = tgt_val_asset2 - val_asset2
    return diff_asset1, diff_asset2

def generate_action_card(col, name, diff, price):
    act = "BUY" if diff > 0 else "SELL"
    color = "green" if diff > 0 else "red"
    if abs(diff) < 10: return col.write(f"✅ {name}: Hold")
    
    amount = abs(diff)/price
    col.markdown(f"""
    <div style="background:#f0f2f6; padding:15px; border-radius:10px; border-left:5px solid {color}">
        <h4 style="margin:0; color:{color}">{name}: {act}</h4>
        <h2 style="margin:0">${abs(diff):,.2f}</h2>
        <p>Units: <b>{amount:.4f}</b></p>
    </div>
    """, unsafe_allow_html=True)
    return f"{act}:{amount:.4f}"

def calculate_rebalance_orders(
    z_score: float,
    z_score_threshold_high: float,
    z_score_threshold_low: float,
    val_asset1: float,
    val_asset2: float,
    tgt_val_asset1: float,
    tgt_val_asset2: float,
    cash_dca: float,
    p_asset1: float,
    p_asset2: float,
    total_val: float
) -> tuple[float, float]:
    """
    Calculates the rebalancing orders based on the Z-score and target allocation.
    
    Args:
        z_score (float): The current Z-score.
        z_score_threshold_high (float): The upper Z-score threshold.
        z_score_threshold_low (float): The lower Z-score threshold.
        val_asset1 (float): The current value of asset 1 holdings.
        val_asset2 (float): The current value of asset 2 holdings.
        tgt_val_asset1 (float): The target value for asset 1.
        tgt_val_asset2 (float): The target value for asset 2.
        cash_dca (float): The amount of cash available.
        p_asset1 (float): The current price of asset 1.
        p_asset2 (float): The current price of asset 2.
        total_val (float): The total portfolio value.

    Returns:
        tuple[float, float]: A tuple containing the difference in value for asset 1 and asset 2.
    """
    if z_score < z_score_threshold_low:  # Asset 2 is cheap, buy Asset 2
        # Use all available cash and any overweight Asset 1 to buy Asset 2
        asset2_buy_amount = cash_dca + max(0, val_asset1 - tgt_val_asset1)
        diff_asset2 = asset2_buy_amount
        
        new_asset2_val = val_asset2 + diff_asset2
        new_asset1_val = total_val - new_asset2_val - cash_dca
        diff_asset1 = new_asset1_val - val_asset1

    elif z_score > z_score_threshold_high:  # Asset 2 is expensive, buy Asset 1
        # Use all available cash and any overweight Asset 2 to buy Asset 1
        asset1_buy_amount = cash_dca + max(0, val_asset2 - tgt_val_asset2)
        diff_asset1 = asset1_buy_amount

        new_asset1_val = val_asset1 + diff_asset1
        new_asset2_val = total_val - new_asset1_val - cash_dca
        diff_asset2 = new_asset2_val - val_asset2

    else:  # Z-score is normal, rebalance to target percentages
        diff_asset1 = tgt_val_asset1 - val_asset1
        diff_asset2 = tgt_val_asset2 - val_asset2
    
    return diff_asset1, diff_asset2