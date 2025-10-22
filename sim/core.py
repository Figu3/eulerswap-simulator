"""
Core simulation engine for Eulerswap LP profitability analysis.
"""

import math
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any
import copy

from sim.models import (
    swap_xy,
    accrue_rate,
    mark_to_market,
    compute_il_vs_hold,
    check_liquidation_risk
)


@dataclass
class PoolState:
    """Current state of the AMM pool and LP position."""
    # Pool reserves
    plusd_reserve: float
    usdt0_reserve: float

    # Trevee LP position
    trevee_plusd: float  # plUSD deposited by Trevee
    trevee_usdt0: float  # USDT0 contribution (may be borrowed)

    # Rehypothecation
    rehypothecated_plusd: float

    # Borrowed amounts
    borrowed_usdt0: float

    # Accumulated metrics
    fee_accruals: float = 0.0
    underlying_yield_accrued: float = 0.0
    rehyp_yield_accrued: float = 0.0
    borrow_cost_accrued: float = 0.0
    ops_cost_accrued: float = 0.0

    # LP share tracking
    initial_trevee_plusd: float = 0.0
    initial_trevee_usdt0: float = 0.0

    # Step counter
    step: int = 0


@dataclass
class SimulationParams:
    """Parameters for simulation run."""
    # Time
    horizon_days: int
    steps_per_day: int
    seed: int

    # AMM
    amm_type: str
    fee_bps: float

    # Yields and costs
    underlying_yield_apr: float
    rehyp_yield_apr: float
    borrow_cost_apr: float
    ops_cost_usd_per_day: float

    # Flow model
    flow_model: str
    deterministic_schedule_bps: float
    stochastic_mu_daily: float = 0.0
    stochastic_sigma_daily: float = 0.25

    # Risk
    max_borrow_multiple: float = 0.8
    peg_deviation_std_bps: float = 5.0

    # Reporting
    mark_plusd_price: float = 1.0
    mark_usdt0_price: float = 1.0

    @property
    def total_steps(self) -> int:
        return self.horizon_days * self.steps_per_day

    @property
    def dt_years(self) -> float:
        """Time step in years."""
        return 1.0 / (365.0 * self.steps_per_day)


@dataclass
class StepResult:
    """Results from a single simulation step."""
    step: int
    time_days: float

    # Pool state
    plusd_reserve: float
    usdt0_reserve: float

    # LP position
    trevee_plusd: float
    trevee_usdt0: float
    lp_share: float

    # Borrowed
    borrowed_usdt0: float
    rehypothecated_plusd: float

    # Flow
    trade_flow: float
    usdt0_out: float

    # Accruals this step
    fee_earned: float
    underlying_yield: float
    rehyp_yield: float
    borrow_cost: float
    ops_cost: float

    # Cumulative
    total_fees: float
    total_underlying_yield: float
    total_rehyp_yield: float
    total_borrow_cost: float
    total_ops_cost: float

    # P&L
    lp_nav: float
    net_pnl: float
    il_absolute: float
    il_percentage: float

    # Risk
    ltv: float
    at_risk: bool


class SimulationEngine:
    """Main simulation engine."""

    def __init__(self, params: SimulationParams, initial_state: PoolState):
        self.params = params
        self.state = initial_state
        self.results: List[StepResult] = []

        # Set RNG seed
        np.random.seed(params.seed)

        # Store initial LP position for IL calculation
        self.state.initial_trevee_plusd = initial_state.trevee_plusd
        self.state.initial_trevee_usdt0 = initial_state.trevee_usdt0

    def generate_trade_flow(self, step: int) -> float:
        """
        Generate trade flow for this step (plUSD → USDT0).

        Returns:
            Amount of plUSD to swap
        """
        if self.params.flow_model == "deterministic":
            # Fixed percentage of pool per step
            pool_size = self.state.plusd_reserve + self.state.usdt0_reserve
            flow_fraction = self.params.deterministic_schedule_bps / 10000.0
            daily_flow = pool_size * flow_fraction

            # Distribute over steps
            flow_per_step = daily_flow / self.params.steps_per_day
            return flow_per_step

        elif self.params.flow_model == "stochastic":
            # Geometric Brownian motion for daily flow
            dt = self.params.dt_years * 365  # Convert to days
            pool_size = self.state.plusd_reserve + self.state.usdt0_reserve

            # Generate random walk
            drift = self.params.stochastic_mu_daily * dt
            diffusion = self.params.stochastic_sigma_daily * math.sqrt(dt) * np.random.randn()

            flow_factor = math.exp(drift + diffusion)
            base_flow = pool_size * 0.01  # 1% base
            return max(0, base_flow * flow_factor)

        else:
            return 0.0

    def execute_swap(self, plusd_in: float) -> float:
        """
        Execute swap: plUSD → USDT0.

        Args:
            plusd_in: Amount of plUSD being swapped

        Returns:
            Amount of USDT0 received
        """
        if plusd_in <= 0:
            return 0.0

        usdt0_out, new_plusd, new_usdt0 = swap_xy(
            self.state.plusd_reserve,
            self.state.usdt0_reserve,
            plusd_in,
            self.params.fee_bps
        )

        # Update reserves
        self.state.plusd_reserve = new_plusd
        self.state.usdt0_reserve = new_usdt0

        return usdt0_out

    def accrue_yields(self) -> Dict[str, float]:
        """
        Accrue yields and costs for this time step.

        Returns:
            Dictionary of accruals
        """
        dt = self.params.dt_years

        # Underlying yield on Trevee's plUSD
        underlying_yield = accrue_rate(
            self.state.trevee_plusd,
            self.params.underlying_yield_apr,
            dt
        )

        # Rehypothecation yield
        rehyp_yield = accrue_rate(
            self.state.rehypothecated_plusd,
            self.params.rehyp_yield_apr,
            dt
        )

        # Borrow cost on USDT0
        borrow_cost = accrue_rate(
            self.state.borrowed_usdt0,
            self.params.borrow_cost_apr,
            dt
        )

        # Operational cost
        ops_cost = self.params.ops_cost_usd_per_day * dt * 365

        # Update state
        self.state.trevee_plusd += underlying_yield
        self.state.underlying_yield_accrued += underlying_yield

        self.state.trevee_plusd += rehyp_yield  # Rehyp yield increases plUSD
        self.state.rehyp_yield_accrued += rehyp_yield

        self.state.borrowed_usdt0 += borrow_cost
        self.state.borrow_cost_accrued += borrow_cost

        self.state.ops_cost_accrued += ops_cost

        return {
            "underlying_yield": underlying_yield,
            "rehyp_yield": rehyp_yield,
            "borrow_cost": borrow_cost,
            "ops_cost": ops_cost
        }

    def calculate_lp_fees(self, trade_volume: float) -> float:
        """
        Calculate LP fees earned from trade volume.

        Args:
            trade_volume: Volume of plUSD traded

        Returns:
            Fee amount in USD
        """
        fee_fraction = self.params.fee_bps / 10000.0
        fee_earned = trade_volume * fee_fraction

        # Fees accrue to LP position (assume proportional to share)
        total_liquidity = self.state.plusd_reserve + self.state.usdt0_reserve
        lp_liquidity = self.state.trevee_plusd + abs(self.state.trevee_usdt0)

        if total_liquidity > 0:
            lp_share = lp_liquidity / total_liquidity
            lp_fee = fee_earned * lp_share
        else:
            lp_fee = 0.0

        self.state.fee_accruals += lp_fee
        return lp_fee

    def calculate_lp_nav(self) -> float:
        """
        Calculate net asset value of Trevee's LP position.

        Returns:
            NAV in USD
        """
        # Mark-to-market value of LP holdings
        asset_value = mark_to_market(
            self.state.trevee_plusd,
            abs(self.state.trevee_usdt0),  # Could be negative if borrowed
            self.params.mark_plusd_price,
            self.params.mark_usdt0_price
        )

        # Subtract borrowed amounts (liability)
        liabilities = self.state.borrowed_usdt0

        nav = asset_value - liabilities

        return nav

    def calculate_pnl(self) -> Dict[str, float]:
        """
        Calculate comprehensive P&L breakdown.

        Returns:
            Dictionary with P&L components
        """
        # Total returns
        total_fees = self.state.fee_accruals
        total_yields = (self.state.underlying_yield_accrued +
                       self.state.rehyp_yield_accrued)

        # Total costs
        total_borrow_cost = self.state.borrow_cost_accrued
        total_ops_cost = self.state.ops_cost_accrued

        # Impermanent loss
        il_metrics = compute_il_vs_hold(
            self.state.initial_trevee_plusd,
            self.state.initial_trevee_usdt0,
            self.state.trevee_plusd,
            self.state.trevee_usdt0,
            self.params.mark_plusd_price,
            self.params.mark_usdt0_price
        )

        # Net P&L
        net_pnl = (total_fees + total_yields -
                  total_borrow_cost - total_ops_cost +
                  il_metrics["il_absolute"])

        return {
            "total_fees": total_fees,
            "total_yields": total_yields,
            "total_borrow_cost": total_borrow_cost,
            "total_ops_cost": total_ops_cost,
            "il_absolute": il_metrics["il_absolute"],
            "il_percentage": il_metrics["il_percentage"],
            "net_pnl": net_pnl
        }

    def step_simulation(self, step: int) -> StepResult:
        """
        Execute one simulation step.

        Args:
            step: Step number

        Returns:
            StepResult with metrics
        """
        # 1. Generate trade flow
        trade_flow = self.generate_trade_flow(step)

        # 2. Execute swap
        usdt0_out = self.execute_swap(trade_flow)

        # 3. Calculate fees from this trade
        fee_earned = self.calculate_lp_fees(trade_flow)

        # 4. Accrue yields and costs
        accruals = self.accrue_yields()

        # 5. Update Trevee's USDT0 position (receives swapped USDT0)
        # In one-sided LP model, this goes toward reducing borrowed position
        if self.state.borrowed_usdt0 > 0:
            repayment = min(usdt0_out, self.state.borrowed_usdt0)
            self.state.borrowed_usdt0 -= repayment
            # Excess goes to LP position
            self.state.trevee_usdt0 += (usdt0_out - repayment)
        else:
            self.state.trevee_usdt0 += usdt0_out

        # 6. Calculate LP share
        total_liquidity = self.state.plusd_reserve + self.state.usdt0_reserve
        lp_liquidity = self.state.trevee_plusd + abs(self.state.trevee_usdt0)
        lp_share = lp_liquidity / total_liquidity if total_liquidity > 0 else 0.0

        # 7. Calculate NAV and P&L
        nav = self.calculate_lp_nav()
        pnl = self.calculate_pnl()

        # 8. Check liquidation risk
        risk = check_liquidation_risk(
            self.state.borrowed_usdt0,
            self.state.trevee_plusd,
            self.params.max_borrow_multiple,
            self.params.mark_plusd_price
        )

        # 9. Create step result
        result = StepResult(
            step=step,
            time_days=step / self.params.steps_per_day,
            plusd_reserve=self.state.plusd_reserve,
            usdt0_reserve=self.state.usdt0_reserve,
            trevee_plusd=self.state.trevee_plusd,
            trevee_usdt0=self.state.trevee_usdt0,
            lp_share=lp_share,
            borrowed_usdt0=self.state.borrowed_usdt0,
            rehypothecated_plusd=self.state.rehypothecated_plusd,
            trade_flow=trade_flow,
            usdt0_out=usdt0_out,
            fee_earned=fee_earned,
            underlying_yield=accruals["underlying_yield"],
            rehyp_yield=accruals["rehyp_yield"],
            borrow_cost=accruals["borrow_cost"],
            ops_cost=accruals["ops_cost"],
            total_fees=pnl["total_fees"],
            total_underlying_yield=self.state.underlying_yield_accrued,
            total_rehyp_yield=self.state.rehyp_yield_accrued,
            total_borrow_cost=pnl["total_borrow_cost"],
            total_ops_cost=pnl["total_ops_cost"],
            lp_nav=nav,
            net_pnl=pnl["net_pnl"],
            il_absolute=pnl["il_absolute"],
            il_percentage=pnl["il_percentage"],
            ltv=risk["ltv"],
            at_risk=risk["at_risk"]
        )

        return result

    def run(self) -> List[StepResult]:
        """
        Run full simulation.

        Returns:
            List of StepResult for each time step
        """
        self.results = []

        # Initial step (t=0)
        initial_result = self.step_simulation(0)
        self.results.append(initial_result)

        # Run remaining steps
        for step in range(1, self.params.total_steps + 1):
            result = self.step_simulation(step)
            self.results.append(result)

        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics from simulation.

        Returns:
            Dictionary with summary metrics
        """
        if not self.results:
            return {}

        final = self.results[-1]

        total_days = self.params.horizon_days
        initial_capital = (self.state.initial_trevee_plusd +
                          self.state.initial_trevee_usdt0)

        # Annualized return
        if initial_capital > 0 and total_days > 0:
            total_return = final.net_pnl / initial_capital
            annualized_return = total_return * (365.0 / total_days)
        else:
            annualized_return = 0.0

        return {
            "horizon_days": total_days,
            "final_nav": final.lp_nav,
            "initial_capital": initial_capital,
            "net_pnl": final.net_pnl,
            "total_return_pct": (final.net_pnl / initial_capital * 100) if initial_capital > 0 else 0,
            "annualized_return_pct": annualized_return * 100,
            "total_fees": final.total_fees,
            "total_yields": final.total_underlying_yield + final.total_rehyp_yield,
            "total_borrow_cost": final.total_borrow_cost,
            "total_ops_cost": final.total_ops_cost,
            "final_il_pct": final.il_percentage,
            "final_borrowed_usdt0": final.borrowed_usdt0,
            "final_ltv": final.ltv,
            "max_drawdown": self._calculate_max_drawdown()
        }

    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown in NAV."""
        if not self.results:
            return 0.0

        peak = self.results[0].lp_nav
        max_dd = 0.0

        for result in self.results:
            if result.lp_nav > peak:
                peak = result.lp_nav

            dd = (peak - result.lp_nav) / peak if peak > 0 else 0.0
            max_dd = max(max_dd, dd)

        return max_dd * 100  # Return as percentage
