#!/usr/bin/env python3
"""
CLI interface to run Eulerswap LP profitability simulations.
"""

import argparse
import yaml
import sys
from pathlib import Path
from typing import Dict, Any

from sim.core import SimulationEngine, SimulationParams, PoolState
from sim.plots import generate_plots


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def create_params_from_config(config: Dict[str, Any]) -> SimulationParams:
    """Create SimulationParams from config dictionary."""
    return SimulationParams(
        horizon_days=config["horizon_days"],
        steps_per_day=config["steps_per_day"],
        seed=config["seed"],
        amm_type=config["amm"]["type"],
        fee_bps=config["amm"]["fee_bps"],
        underlying_yield_apr=config["yields"]["underlying_yield_apr"],
        rehyp_yield_apr=config["yields"]["rehyp_yield_apr"],
        borrow_cost_apr=config["yields"]["borrow_cost_apr"],
        ops_cost_usd_per_day=config["costs"]["ops_cost_usd_per_day"],
        flow_model=config["flow"]["model"],
        deterministic_schedule_bps=config["flow"].get("deterministic_schedule_bps_of_pool", 20),
        stochastic_mu_daily=config["flow"]["stochastic"].get("mu_daily", 0.0),
        stochastic_sigma_daily=config["flow"]["stochastic"].get("sigma_daily", 0.25),
        max_borrow_multiple=config["risk"]["max_borrow_multiple"],
        peg_deviation_std_bps=config["yields"]["peg_deviation_std_bps"],
        mark_plusd_price=config["reporting"]["mark_to_market_price_plusd"],
        mark_usdt0_price=config["reporting"]["mark_to_market_price_usdt0"]
    )


def create_initial_state_from_config(config: Dict[str, Any]) -> PoolState:
    """Create initial PoolState from config dictionary."""
    init = config["initial_state"]

    # Calculate borrowed USDT0 if Trevee only deposits plUSD
    # Assume pool needs balanced liquidity, so USDT0 is borrowed
    trevee_usdt0_contribution = 0.0  # Trevee deposits only plUSD
    borrowed_usdt0 = init["usdt0_reserve"] - trevee_usdt0_contribution

    # Rehypothecated plUSD
    rehyp_fraction = init.get("rehyp_fraction", 0.6)
    rehypothecated_plusd = init["trevee_deposit_plusd"] * rehyp_fraction

    return PoolState(
        plusd_reserve=init["plusd_reserve"],
        usdt0_reserve=init["usdt0_reserve"],
        trevee_plusd=init["trevee_deposit_plusd"],
        trevee_usdt0=trevee_usdt0_contribution,
        rehypothecated_plusd=rehypothecated_plusd,
        borrowed_usdt0=borrowed_usdt0,
        fee_accruals=0.0,
        underlying_yield_accrued=0.0,
        rehyp_yield_accrued=0.0,
        borrow_cost_accrued=0.0,
        ops_cost_accrued=0.0,
        initial_trevee_plusd=init["trevee_deposit_plusd"],
        initial_trevee_usdt0=trevee_usdt0_contribution,
        step=0
    )


def print_summary(summary: Dict[str, Any], verbose: bool = False):
    """Print simulation summary to console."""
    print("\n" + "="*60)
    print("SIMULATION SUMMARY")
    print("="*60)

    print(f"\nTime Horizon: {summary['horizon_days']} days")
    print(f"Initial Capital: ${summary['initial_capital']:,.2f}")
    print(f"Final NAV: ${summary['final_nav']:,.2f}")

    print(f"\n{'P&L BREAKDOWN':-^60}")
    print(f"Total Fees Earned: ${summary['total_fees']:,.2f}")
    print(f"Total Yields: ${summary['total_yields']:,.2f}")
    print(f"Total Borrow Cost: -${summary['total_borrow_cost']:,.2f}")
    print(f"Total Ops Cost: -${summary['total_ops_cost']:,.2f}")
    print(f"Impermanent Loss: {summary['final_il_pct']:.2f}%")
    print(f"{'-'*60}")
    print(f"Net P&L: ${summary['net_pnl']:,.2f}")

    print(f"\n{'RETURNS':-^60}")
    print(f"Total Return: {summary['total_return_pct']:.2f}%")
    print(f"Annualized Return: {summary['annualized_return_pct']:.2f}%")
    print(f"Max Drawdown: {summary['max_drawdown']:.2f}%")

    print(f"\n{'RISK METRICS':-^60}")
    print(f"Final Borrowed USDT0: ${summary['final_borrowed_usdt0']:,.2f}")
    print(f"Final LTV: {summary['final_ltv']:.2%}")

    print("\n" + "="*60 + "\n")

    if verbose:
        print("\nDetailed metrics available in results object.")


def export_results(results, output_path: str, format: str = "csv"):
    """Export simulation results to file."""
    import csv
    import json

    if format == "csv":
        with open(output_path, 'w', newline='') as f:
            if not results:
                return

            fieldnames = [
                'step', 'time_days', 'plusd_reserve', 'usdt0_reserve',
                'trevee_plusd', 'trevee_usdt0', 'borrowed_usdt0',
                'trade_flow', 'usdt0_out', 'fee_earned',
                'underlying_yield', 'rehyp_yield', 'borrow_cost', 'ops_cost',
                'lp_nav', 'net_pnl', 'il_percentage', 'ltv'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for r in results:
                writer.writerow({
                    'step': r.step,
                    'time_days': r.time_days,
                    'plusd_reserve': r.plusd_reserve,
                    'usdt0_reserve': r.usdt0_reserve,
                    'trevee_plusd': r.trevee_plusd,
                    'trevee_usdt0': r.trevee_usdt0,
                    'borrowed_usdt0': r.borrowed_usdt0,
                    'trade_flow': r.trade_flow,
                    'usdt0_out': r.usdt0_out,
                    'fee_earned': r.fee_earned,
                    'underlying_yield': r.underlying_yield,
                    'rehyp_yield': r.rehyp_yield,
                    'borrow_cost': r.borrow_cost,
                    'ops_cost': r.ops_cost,
                    'lp_nav': r.lp_nav,
                    'net_pnl': r.net_pnl,
                    'il_percentage': r.il_percentage,
                    'ltv': r.ltv
                })

        print(f"Results exported to {output_path}")

    elif format == "json":
        data = []
        for r in results:
            data.append({
                'step': r.step,
                'time_days': r.time_days,
                'plusd_reserve': r.plusd_reserve,
                'usdt0_reserve': r.usdt0_reserve,
                'trevee_plusd': r.trevee_plusd,
                'trevee_usdt0': r.trevee_usdt0,
                'borrowed_usdt0': r.borrowed_usdt0,
                'trade_flow': r.trade_flow,
                'usdt0_out': r.usdt0_out,
                'fee_earned': r.fee_earned,
                'underlying_yield': r.underlying_yield,
                'rehyp_yield': r.rehyp_yield,
                'borrow_cost': r.borrow_cost,
                'ops_cost': r.ops_cost,
                'lp_nav': r.lp_nav,
                'net_pnl': r.net_pnl,
                'il_percentage': r.il_percentage,
                'ltv': r.ltv
            })

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Results exported to {output_path}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Eulerswap LP Profitability Simulator"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="sim/config.yaml",
        help="Path to configuration YAML file (default: sim/config.yaml)"
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Export results to file (CSV or JSON based on extension)"
    )

    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate performance plots"
    )

    parser.add_argument(
        "--plot-output",
        type=str,
        default="output/simulation_results.png",
        help="Path for plot output (default: output/simulation_results.png)"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Minimal output (summary only)"
    )

    args = parser.parse_args()

    # Load config
    if not Path(args.config).exists():
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Loading configuration from {args.config}...")

    config = load_config(args.config)

    # Create params and initial state
    params = create_params_from_config(config)
    initial_state = create_initial_state_from_config(config)

    # Run simulation
    if not args.quiet:
        print(f"Running simulation for {params.horizon_days} days...")
        print(f"Time steps: {params.total_steps}")

    engine = SimulationEngine(params, initial_state)
    results = engine.run()

    if not args.quiet:
        print(f"Simulation complete. {len(results)} steps executed.")

    # Get summary
    summary = engine.get_summary()

    # Print summary
    if not args.quiet:
        print_summary(summary, verbose=args.verbose)
    else:
        # Minimal output
        print(f"Net P&L: ${summary['net_pnl']:,.2f} | "
              f"Return: {summary['total_return_pct']:.2f}% | "
              f"APR: {summary['annualized_return_pct']:.2f}%")

    # Export results
    if args.output:
        format = "json" if args.output.endswith(".json") else "csv"
        export_results(results, args.output, format=format)

    # Generate plots
    if args.plot:
        if not args.quiet:
            print(f"Generating plots...")

        output_path = Path(args.plot_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generate_plots(results, summary, str(output_path))

        if not args.quiet:
            print(f"Plots saved to {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
