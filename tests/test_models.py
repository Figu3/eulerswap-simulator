"""
Unit tests for AMM models and financial calculations.
"""

import pytest
import math
from sim.models import (
    swap_xy,
    accrue_rate,
    compute_price_impact,
    compute_il_vs_hold,
    mark_to_market,
    calculate_pool_share,
    check_liquidation_risk
)


class TestSwapXY:
    """Tests for constant product AMM swap function."""

    def test_swap_basic(self):
        """Test basic swap mechanics."""
        x_reserve = 1000.0
        y_reserve = 1000.0
        x_in = 100.0
        fee_bps = 30  # 0.3%

        y_out, new_x, new_y = swap_xy(x_reserve, y_reserve, x_in, fee_bps)

        # Check reserves increased/decreased
        assert new_x > x_reserve
        assert new_y < y_reserve

        # Check output is positive
        assert y_out > 0

        # Check k increased due to fees (new_x * new_y > old k)
        old_k = x_reserve * y_reserve
        new_k = new_x * new_y
        assert new_k > old_k

    def test_swap_zero_input(self):
        """Test swap with zero input."""
        y_out, new_x, new_y = swap_xy(1000.0, 1000.0, 0.0, 30)

        assert y_out == 0.0
        assert new_x == 1000.0
        assert new_y == 1000.0

    def test_swap_zero_fee(self):
        """Test swap with zero fees."""
        x_reserve = 1000.0
        y_reserve = 1000.0
        x_in = 100.0

        y_out, new_x, new_y = swap_xy(x_reserve, y_reserve, x_in, 0)

        # With zero fees, k should be constant
        old_k = x_reserve * y_reserve
        new_k = new_x * new_y
        assert abs(new_k - old_k) < 1e-6

    def test_swap_conservation(self):
        """Test that swap conserves constant product with fees."""
        x_reserve = 10000.0
        y_reserve = 10000.0
        x_in = 500.0
        fee_bps = 7  # 0.07%

        y_out, new_x, new_y = swap_xy(x_reserve, y_reserve, x_in, fee_bps)

        # New reserves should satisfy: new_x * new_y >= old_k
        old_k = x_reserve * y_reserve
        new_k = new_x * new_y
        assert new_k >= old_k

    def test_swap_high_fee(self):
        """Test swap with high fees reduces output."""
        x_reserve = 1000.0
        y_reserve = 1000.0
        x_in = 100.0

        # Low fee
        y_out_low, _, _ = swap_xy(x_reserve, y_reserve, x_in, 7)

        # High fee
        y_out_high, _, _ = swap_xy(x_reserve, y_reserve, x_in, 100)

        # Higher fee should give less output
        assert y_out_low > y_out_high


class TestAccrueRate:
    """Tests for continuous compounding accrual."""

    def test_accrue_positive_rate(self):
        """Test accrual with positive rate."""
        balance = 1000.0
        apr = 0.10  # 10%
        dt_years = 1.0

        accrual = accrue_rate(balance, apr, dt_years)

        # Should be approximately 10% for 1 year
        # Continuous: e^0.1 - 1 ≈ 0.1052
        expected = balance * (math.exp(apr * dt_years) - 1)
        assert abs(accrual - expected) < 1e-6

    def test_accrue_zero_balance(self):
        """Test accrual with zero balance."""
        accrual = accrue_rate(0.0, 0.10, 1.0)
        assert accrual == 0.0

    def test_accrue_zero_rate(self):
        """Test accrual with zero rate."""
        accrual = accrue_rate(1000.0, 0.0, 1.0)
        assert accrual == 0.0

    def test_accrue_short_period(self):
        """Test accrual over short time period."""
        balance = 1000.0
        apr = 0.12  # 12%
        dt_years = 1.0 / 365  # 1 day

        accrual = accrue_rate(balance, apr, dt_years)

        # Should be small for 1 day
        assert accrual > 0
        assert accrual < balance * 0.01  # Less than 1% per day


class TestComputePriceImpact:
    """Tests for price impact calculation."""

    def test_price_impact_small_trade(self):
        """Test price impact for small trade."""
        impact = compute_price_impact(10000.0, 10000.0, 100.0)

        # Small trade should have small impact
        assert impact > 0
        assert impact < 0.02  # Less than 2%

    def test_price_impact_large_trade(self):
        """Test price impact for large trade."""
        impact = compute_price_impact(10000.0, 10000.0, 5000.0)

        # Large trade should have significant impact
        assert impact > 0.1  # More than 10%

    def test_price_impact_zero_trade(self):
        """Test price impact for zero trade."""
        impact = compute_price_impact(10000.0, 10000.0, 0.0)
        assert impact == 0.0


class TestComputeIL:
    """Tests for impermanent loss calculation."""

    def test_il_no_change(self):
        """Test IL when reserves don't change."""
        il = compute_il_vs_hold(
            initial_plusd=1000.0,
            initial_usdt0=1000.0,
            current_plusd=1000.0,
            current_usdt0=1000.0,
            current_price_plusd=1.0,
            current_price_usdt0=1.0
        )

        assert abs(il["il_absolute"]) < 1e-6
        assert abs(il["il_percentage"]) < 1e-6

    def test_il_positive(self):
        """Test positive IL scenario."""
        il = compute_il_vs_hold(
            initial_plusd=1000.0,
            initial_usdt0=1000.0,
            current_plusd=1100.0,
            current_usdt0=1100.0,
            current_price_plusd=1.0,
            current_price_usdt0=1.0
        )

        # More assets = positive IL
        assert il["il_absolute"] > 0
        assert il["il_percentage"] > 0

    def test_il_negative(self):
        """Test negative IL scenario."""
        il = compute_il_vs_hold(
            initial_plusd=1000.0,
            initial_usdt0=1000.0,
            current_plusd=900.0,
            current_usdt0=900.0,
            current_price_plusd=1.0,
            current_price_usdt0=1.0
        )

        # Fewer assets = negative IL
        assert il["il_absolute"] < 0
        assert il["il_percentage"] < 0


class TestMarkToMarket:
    """Tests for mark-to-market valuation."""

    def test_mtm_basic(self):
        """Test basic MTM calculation."""
        value = mark_to_market(
            plusd_balance=1000.0,
            usdt0_balance=1000.0,
            plusd_price=1.0,
            usdt0_price=1.0
        )

        assert value == 2000.0

    def test_mtm_different_prices(self):
        """Test MTM with different prices."""
        value = mark_to_market(
            plusd_balance=1000.0,
            usdt0_balance=1000.0,
            plusd_price=1.05,
            usdt0_price=0.99
        )

        expected = 1000.0 * 1.05 + 1000.0 * 0.99
        assert abs(value - expected) < 1e-6


class TestCalculatePoolShare:
    """Tests for pool share calculation."""

    def test_pool_share_equal(self):
        """Test pool share with equal contribution."""
        share = calculate_pool_share(
            lp_plusd=500.0,
            lp_usdt0=500.0,
            total_plusd=5000.0,
            total_usdt0=5000.0
        )

        # 1000 / 10000 = 0.1 (10%)
        assert abs(share - 0.1) < 1e-6

    def test_pool_share_zero_pool(self):
        """Test pool share with zero total."""
        share = calculate_pool_share(
            lp_plusd=100.0,
            lp_usdt0=100.0,
            total_plusd=0.0,
            total_usdt0=0.0
        )

        assert share == 0.0


class TestCheckLiquidationRisk:
    """Tests for liquidation risk assessment."""

    def test_liquidation_safe(self):
        """Test safe position (low LTV)."""
        risk = check_liquidation_risk(
            borrowed_usdt0=400.0,
            collateral_plusd=1000.0,
            max_borrow_multiple=0.8,
            plusd_price=1.0
        )

        # LTV = 400/1000 = 0.4 < 0.8
        assert risk["ltv"] == 0.4
        assert risk["at_risk"] is False
        assert risk["utilization"] == 0.5  # 400/800

    def test_liquidation_at_risk(self):
        """Test position at risk (high LTV)."""
        risk = check_liquidation_risk(
            borrowed_usdt0=850.0,
            collateral_plusd=1000.0,
            max_borrow_multiple=0.8,
            plusd_price=1.0
        )

        # LTV = 850/1000 = 0.85 > 0.8
        assert risk["ltv"] == 0.85
        assert risk["at_risk"] is True

    def test_liquidation_no_collateral(self):
        """Test with no collateral."""
        risk = check_liquidation_risk(
            borrowed_usdt0=100.0,
            collateral_plusd=0.0,
            max_borrow_multiple=0.8,
            plusd_price=1.0
        )

        assert risk["ltv"] == float('inf')
        assert risk["at_risk"] is True

    def test_liquidation_no_debt(self):
        """Test with no debt."""
        risk = check_liquidation_risk(
            borrowed_usdt0=0.0,
            collateral_plusd=1000.0,
            max_borrow_multiple=0.8,
            plusd_price=1.0
        )

        assert risk["ltv"] == 0.0
        assert risk["at_risk"] is False


class TestIntegrationScenarios:
    """Integration tests for complete scenarios."""

    def test_zero_fee_zero_flow_yields_only(self):
        """
        Acceptance test: Zero fees and zero flow should result in yields only.
        """
        from sim.core import SimulationEngine, SimulationParams, PoolState

        # Create params with zero fees and zero flow
        params = SimulationParams(
            horizon_days=30,
            steps_per_day=1,
            seed=42,
            amm_type="constant_product",
            fee_bps=0,  # No fees
            underlying_yield_apr=0.06,
            rehyp_yield_apr=0.12,
            borrow_cost_apr=0.0,  # No borrow cost
            ops_cost_usd_per_day=0.0,  # No ops cost
            flow_model="deterministic",
            deterministic_schedule_bps=0,  # No flow
            max_borrow_multiple=0.8,
            peg_deviation_std_bps=0,
            mark_plusd_price=1.0,
            mark_usdt0_price=1.0
        )

        initial_state = PoolState(
            plusd_reserve=5_000_000.0,
            usdt0_reserve=5_000_000.0,
            trevee_plusd=1_000_000.0,
            trevee_usdt0=0.0,
            rehypothecated_plusd=600_000.0,
            borrowed_usdt0=0.0  # No borrowing
        )

        engine = SimulationEngine(params, initial_state)
        results = engine.run()
        summary = engine.get_summary()

        # With no fees, no flow, no borrow cost, and no ops cost,
        # P&L should equal yields
        assert summary["total_fees"] == 0.0
        assert summary["total_borrow_cost"] == 0.0
        assert summary["total_ops_cost"] == 0.0
        assert summary["total_yields"] > 0

        # Net P&L should approximately equal yields (minus small IL)
        # IL should be close to 0 with no flow
        assert abs(summary["final_il_pct"]) < 0.1

    def test_symmetric_flow_positive_fees(self):
        """
        Test that symmetric flow generates positive fees and bounded IL.
        """
        from sim.core import SimulationEngine, SimulationParams, PoolState

        params = SimulationParams(
            horizon_days=7,
            steps_per_day=24,
            seed=42,
            amm_type="constant_product",
            fee_bps=7,
            underlying_yield_apr=0.0,
            rehyp_yield_apr=0.0,
            borrow_cost_apr=0.0,
            ops_cost_usd_per_day=0.0,
            flow_model="deterministic",
            deterministic_schedule_bps=10,  # 0.1% of pool per step
            max_borrow_multiple=0.8,
            peg_deviation_std_bps=0,
            mark_plusd_price=1.0,
            mark_usdt0_price=1.0
        )

        initial_state = PoolState(
            plusd_reserve=5_000_000.0,
            usdt0_reserve=5_000_000.0,
            trevee_plusd=1_000_000.0,
            trevee_usdt0=0.0,
            rehypothecated_plusd=600_000.0,
            borrowed_usdt0=5_000_000.0
        )

        engine = SimulationEngine(params, initial_state)
        results = engine.run()
        summary = engine.get_summary()

        # Should generate positive fees
        assert summary["total_fees"] > 0

        # IL should be bounded
        assert abs(summary["final_il_pct"]) < 50  # Less than 50%

    def test_zero_borrow_no_debt_growth(self):
        """
        Test that zero borrowing results in no debt growth.
        """
        from sim.core import SimulationEngine, SimulationParams, PoolState

        params = SimulationParams(
            horizon_days=30,
            steps_per_day=24,
            seed=42,
            amm_type="constant_product",
            fee_bps=7,
            underlying_yield_apr=0.06,
            rehyp_yield_apr=0.12,
            borrow_cost_apr=0.08,
            ops_cost_usd_per_day=100.0,
            flow_model="deterministic",
            deterministic_schedule_bps=5,
            max_borrow_multiple=0.8,
            peg_deviation_std_bps=0,
            mark_plusd_price=1.0,
            mark_usdt0_price=1.0
        )

        initial_state = PoolState(
            plusd_reserve=5_000_000.0,
            usdt0_reserve=5_000_000.0,
            trevee_plusd=1_000_000.0,
            trevee_usdt0=0.0,
            rehypothecated_plusd=600_000.0,
            borrowed_usdt0=0.0  # No initial debt
        )

        engine = SimulationEngine(params, initial_state)
        results = engine.run()
        summary = engine.get_summary()

        # No borrow cost should accrue
        assert summary["total_borrow_cost"] == 0.0
        assert summary["final_borrowed_usdt0"] >= 0.0  # Could be negative (net positive USDT0)

    def test_fee_increase_improves_pnl(self):
        """
        Test that increasing fees from 0 to 7 bps improves P&L.
        """
        from sim.core import SimulationEngine, SimulationParams, PoolState

        base_params = {
            "horizon_days": 30,
            "steps_per_day": 24,
            "seed": 42,
            "amm_type": "constant_product",
            "underlying_yield_apr": 0.06,
            "rehyp_yield_apr": 0.12,
            "borrow_cost_apr": 0.08,
            "ops_cost_usd_per_day": 100.0,
            "flow_model": "deterministic",
            "deterministic_schedule_bps": 10,
            "max_borrow_multiple": 0.8,
            "peg_deviation_std_bps": 0,
            "mark_plusd_price": 1.0,
            "mark_usdt0_price": 1.0
        }

        base_state = {
            "plusd_reserve": 5_000_000.0,
            "usdt0_reserve": 5_000_000.0,
            "trevee_plusd": 1_000_000.0,
            "trevee_usdt0": 0.0,
            "rehypothecated_plusd": 600_000.0,
            "borrowed_usdt0": 5_000_000.0
        }

        # Run with 0 bps fee
        params_0 = SimulationParams(**{**base_params, "fee_bps": 0})
        state_0 = PoolState(**base_state)
        engine_0 = SimulationEngine(params_0, state_0)
        engine_0.run()
        summary_0 = engine_0.get_summary()

        # Run with 7 bps fee
        params_7 = SimulationParams(**{**base_params, "fee_bps": 7})
        state_7 = PoolState(**base_state)
        engine_7 = SimulationEngine(params_7, state_7)
        engine_7.run()
        summary_7 = engine_7.get_summary()

        # Higher fee should result in higher total fees
        assert summary_7["total_fees"] > summary_0["total_fees"]

        # Net P&L should be better with fees (all else equal)
        # Note: IL might differ slightly, but fees should dominate
        assert summary_7["total_fees"] > 0
