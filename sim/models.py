"""
AMM math functions and financial calculations for Eulerswap simulator.
"""

import math
from typing import Tuple


def swap_xy(x_reserve: float, y_reserve: float, x_in: float, fee_bps: float) -> Tuple[float, float, float]:
    """
    Constant-product AMM swap: x * y = k

    Args:
        x_reserve: Reserve of token X (input token)
        y_reserve: Reserve of token Y (output token)
        x_in: Amount of X being swapped in
        fee_bps: Fee in basis points (e.g., 7 for 0.07%)

    Returns:
        Tuple of (y_out, new_x_reserve, new_y_reserve)
    """
    if x_in <= 0:
        return 0.0, x_reserve, y_reserve

    # Calculate fee (x_in_after_fee = x_in * (1 - fee))
    fee_fraction = fee_bps / 10000.0
    x_in_after_fee = x_in * (1.0 - fee_fraction)

    # Constant product: k = x * y
    k = x_reserve * y_reserve

    # New X reserve after adding input
    new_x = x_reserve + x_in_after_fee

    # Calculate new Y reserve to maintain k
    new_y = k / new_x

    # Amount of Y going out
    y_out = y_reserve - new_y

    # Actual new reserves (fee stays in pool)
    actual_new_x = x_reserve + x_in  # Full x_in goes to reserve

    return y_out, actual_new_x, new_y


def accrue_rate(balance: float, apr: float, dt_years: float) -> float:
    """
    Calculate continuous compounding accrual.

    Args:
        balance: Initial balance
        apr: Annual percentage rate (as decimal, e.g., 0.06 for 6%)
        dt_years: Time step in years

    Returns:
        Accrued interest amount (not including principal)
    """
    if balance <= 0 or apr == 0:
        return 0.0

    # Continuous compounding: A = P * e^(r*t)
    new_balance = balance * math.exp(apr * dt_years)
    accrual = new_balance - balance

    return accrual


def compute_price_impact(x_reserve: float, y_reserve: float, x_in: float) -> float:
    """
    Calculate price impact of a swap as percentage.

    Args:
        x_reserve: Reserve of input token
        y_reserve: Reserve of output token
        x_in: Amount being swapped

    Returns:
        Price impact as decimal (e.g., 0.02 for 2%)
    """
    if x_in <= 0:
        return 0.0

    # Spot price before: y/x
    price_before = y_reserve / x_reserve

    # Effective price: y_out / x_in (ignoring fees)
    k = x_reserve * y_reserve
    new_x = x_reserve + x_in
    new_y = k / new_x
    y_out = y_reserve - new_y
    price_effective = y_out / x_in if x_in > 0 else price_before

    # Impact as percentage difference
    impact = abs(price_effective - price_before) / price_before

    return impact


def compute_il_vs_hold(
    initial_plusd: float,
    initial_usdt0: float,
    current_plusd: float,
    current_usdt0: float,
    current_price_plusd: float,
    current_price_usdt0: float
) -> dict:
    """
    Calculate impermanent loss vs. holding assets.

    Args:
        initial_plusd: Initial plUSD in LP position
        initial_usdt0: Initial USDT0 in LP position
        current_plusd: Current plUSD in LP position
        current_usdt0: Current USDT0 in LP position
        current_price_plusd: Mark-to-market price of plUSD
        current_price_usdt0: Mark-to-market price of USDT0

    Returns:
        Dictionary with IL metrics
    """
    # Value if held (HODL value)
    hodl_value = (initial_plusd * current_price_plusd +
                  initial_usdt0 * current_price_usdt0)

    # Current LP value
    lp_value = (current_plusd * current_price_plusd +
                current_usdt0 * current_price_usdt0)

    # Impermanent loss
    il_absolute = lp_value - hodl_value
    il_percentage = (il_absolute / hodl_value * 100) if hodl_value > 0 else 0.0

    return {
        "hodl_value": hodl_value,
        "lp_value": lp_value,
        "il_absolute": il_absolute,
        "il_percentage": il_percentage
    }


def mark_to_market(
    plusd_balance: float,
    usdt0_balance: float,
    plusd_price: float,
    usdt0_price: float
) -> float:
    """
    Calculate mark-to-market value of holdings.

    Args:
        plusd_balance: Amount of plUSD
        usdt0_balance: Amount of USDT0
        plusd_price: Price of plUSD
        usdt0_price: Price of USDT0

    Returns:
        Total USD value
    """
    return plusd_balance * plusd_price + usdt0_balance * usdt0_price


def calculate_pool_share(
    lp_plusd: float,
    lp_usdt0: float,
    total_plusd: float,
    total_usdt0: float
) -> float:
    """
    Calculate LP's share of the pool.

    Args:
        lp_plusd: LP's plUSD contribution
        lp_usdt0: LP's USDT0 contribution
        total_plusd: Total plUSD in pool
        total_usdt0: Total USDT0 in pool

    Returns:
        Share as decimal (e.g., 0.2 for 20%)
    """
    lp_value = lp_plusd + lp_usdt0  # Assuming 1:1 peg
    total_value = total_plusd + total_usdt0

    if total_value <= 0:
        return 0.0

    return lp_value / total_value


def check_liquidation_risk(
    borrowed_usdt0: float,
    collateral_plusd: float,
    max_borrow_multiple: float,
    plusd_price: float = 1.0
) -> dict:
    """
    Check if position is at risk of liquidation.

    Args:
        borrowed_usdt0: Amount of USDT0 borrowed
        collateral_plusd: Amount of plUSD collateral
        max_borrow_multiple: Maximum allowed LTV ratio
        plusd_price: Price of plUSD (default 1.0)

    Returns:
        Dictionary with liquidation risk metrics
    """
    collateral_value = collateral_plusd * plusd_price

    if collateral_value <= 0:
        return {
            "ltv": float('inf') if borrowed_usdt0 > 0 else 0.0,
            "at_risk": borrowed_usdt0 > 0,
            "utilization": 1.0 if borrowed_usdt0 > 0 else 0.0
        }

    ltv = borrowed_usdt0 / collateral_value
    max_borrow = collateral_value * max_borrow_multiple
    utilization = borrowed_usdt0 / max_borrow if max_borrow > 0 else 0.0

    return {
        "ltv": ltv,
        "at_risk": ltv >= max_borrow_multiple,
        "utilization": utilization,
        "max_borrow": max_borrow
    }
