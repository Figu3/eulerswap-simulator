#!/usr/bin/env python3
"""
Compare multiple simulation scenarios side-by-side.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sim.core import SimulationEngine, SimulationParams, PoolState
from sim.run import load_config, create_params_from_config, create_initial_state_from_config


def run_scenario(config_path: str, name: str):
    """Run a single scenario and return summary."""
    config = load_config(config_path)
    params = create_params_from_config(config)
    initial_state = create_initial_state_from_config(config)

    engine = SimulationEngine(params, initial_state)
    engine.run()
    summary = engine.get_summary()

    return {
        "name": name,
        "summary": summary,
        "params": params
    }


def print_comparison(scenarios):
    """Print side-by-side comparison."""
    print("\n" + "="*100)
    print("SCENARIO COMPARISON")
    print("="*100)

    # Header
    print(f"\n{'Metric':<30}", end="")
    for s in scenarios:
        print(f"{s['name']:<23}", end="")
    print()
    print("-"*100)

    # Metrics
    metrics = [
        ("Horizon (days)", lambda s: s["summary"]["horizon_days"]),
        ("Initial Capital", lambda s: f"${s['summary']['initial_capital']:,.0f}"),
        ("Final NAV", lambda s: f"${s['summary']['final_nav']:,.0f}"),
        ("", lambda s: ""),
        ("Total Fees", lambda s: f"${s['summary']['total_fees']:,.0f}"),
        ("Total Yields", lambda s: f"${s['summary']['total_yields']:,.0f}"),
        ("Borrow Cost", lambda s: f"-${s['summary']['total_borrow_cost']:,.0f}"),
        ("Ops Cost", lambda s: f"-${s['summary']['total_ops_cost']:,.0f}"),
        ("IL %", lambda s: f"{s['summary']['final_il_pct']:.2f}%"),
        ("", lambda s: ""),
        ("Net P&L", lambda s: f"${s['summary']['net_pnl']:,.0f}"),
        ("Total Return", lambda s: f"{s['summary']['total_return_pct']:.2f}%"),
        ("Annual Return", lambda s: f"{s['summary']['annualized_return_pct']:.2f}%"),
        ("Max Drawdown", lambda s: f"{s['summary']['max_drawdown']:.2f}%"),
        ("", lambda s: ""),
        ("Fee Rate (bps)", lambda s: f"{s['params'].fee_bps}"),
        ("Flow Rate (bps)", lambda s: f"{s['params'].deterministic_schedule_bps}"),
        ("Rehyp Fraction", lambda s: f"{s['params'].rehyp_yield_apr:.1%}"),
        ("Final LTV", lambda s: f"{s['summary']['final_ltv']:.1%}"),
    ]

    for label, getter in metrics:
        if label == "":
            print()
            continue

        print(f"{label:<30}", end="")
        for s in scenarios:
            value = getter(s)
            print(f"{str(value):<23}", end="")
        print()

    print("\n" + "="*100)

    # Recommendations
    print("\nRECOMMENDATIONS:")

    # Find best by different metrics
    best_return = max(scenarios, key=lambda s: s['summary']['annualized_return_pct'])
    best_fees = max(scenarios, key=lambda s: s['summary']['total_fees'])
    safest_ltv = min(scenarios, key=lambda s: s['summary']['final_ltv'])

    print(f"  • Best Annual Return: {best_return['name']} ({best_return['summary']['annualized_return_pct']:.2f}%)")
    print(f"  • Most Fees Earned: {best_fees['name']} (${best_fees['summary']['total_fees']:,.0f})")
    print(f"  • Lowest Risk (LTV): {safest_ltv['name']} ({safest_ltv['summary']['final_ltv']:.1%})")

    print("\n")


def main():
    """Compare default scenarios."""
    scenarios = [
        run_scenario("sim/config.yaml", "Default"),
        run_scenario("sim/config_profitable.yaml", "Profitable"),
        run_scenario("sim/config_high_volume.yaml", "High Volume"),
        run_scenario("sim/config_optimized.yaml", "Optimized"),
    ]

    print_comparison(scenarios)


if __name__ == "__main__":
    main()
