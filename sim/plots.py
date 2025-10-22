"""
Visualization tools for simulation results.
"""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from typing import List, Dict, Any
from pathlib import Path

from sim.core import StepResult


def generate_plots(results: List[StepResult], summary: Dict[str, Any], output_path: str):
    """
    Generate comprehensive performance plots.

    Args:
        results: List of simulation step results
        summary: Summary statistics dictionary
        output_path: Path to save the plot
    """
    if not results:
        print("No results to plot")
        return

    # Set style
    plt.style.use('dark_background')

    # Create figure with subplots
    fig = plt.figure(figsize=(16, 12))
    gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.3, wspace=0.3)

    # Extract time series data
    time_days = [r.time_days for r in results]
    nav = [r.lp_nav for r in results]
    net_pnl = [r.net_pnl for r in results]

    # P&L components (cumulative)
    fees = [r.total_fees for r in results]
    underlying_yield = [r.total_underlying_yield for r in results]
    rehyp_yield = [r.total_rehyp_yield for r in results]
    borrow_cost = [-r.total_borrow_cost for r in results]  # Negative
    ops_cost = [-r.total_ops_cost for r in results]  # Negative
    il = [r.il_absolute for r in results]

    borrowed = [r.borrowed_usdt0 for r in results]
    ltv = [r.ltv * 100 for r in results]  # Convert to percentage

    # 1. LP NAV Over Time
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(time_days, nav, linewidth=2, color='#00ff88', label='LP NAV')
    ax1.axhline(y=summary['initial_capital'], color='#ff6b6b',
                linestyle='--', alpha=0.5, label='Initial Capital')
    ax1.fill_between(time_days, summary['initial_capital'], nav,
                     where=np.array(nav) >= summary['initial_capital'],
                     alpha=0.2, color='#00ff88', label='Profit')
    ax1.fill_between(time_days, summary['initial_capital'], nav,
                     where=np.array(nav) < summary['initial_capital'],
                     alpha=0.2, color='#ff6b6b', label='Loss')
    ax1.set_xlabel('Days')
    ax1.set_ylabel('USD')
    ax1.set_title('LP Net Asset Value (NAV)', fontweight='bold', fontsize=12)
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.2)
    format_axis(ax1)

    # 2. P&L Component Breakdown (Stacked Area)
    ax2 = fig.add_subplot(gs[0, 1])

    # Positive components
    ax2.fill_between(time_days, 0, fees, alpha=0.7, color='#4ecdc4', label='Fees')
    ax2.fill_between(time_days, fees,
                     np.array(fees) + np.array(underlying_yield),
                     alpha=0.7, color='#95e1d3', label='Underlying Yield')
    ax2.fill_between(time_days,
                     np.array(fees) + np.array(underlying_yield),
                     np.array(fees) + np.array(underlying_yield) + np.array(rehyp_yield),
                     alpha=0.7, color='#f38181', label='Rehyp Yield')

    # Negative components
    ax2.fill_between(time_days, 0, borrow_cost, alpha=0.7, color='#aa4465', label='Borrow Cost')
    ax2.fill_between(time_days, borrow_cost,
                     np.array(borrow_cost) + np.array(ops_cost),
                     alpha=0.7, color='#662549', label='Ops Cost')

    # Net P&L line
    ax2.plot(time_days, net_pnl, linewidth=2.5, color='#ffd93d',
            label='Net P&L', linestyle='-', marker='', zorder=10)

    ax2.axhline(y=0, color='white', linestyle='-', alpha=0.3)
    ax2.set_xlabel('Days')
    ax2.set_ylabel('USD')
    ax2.set_title('P&L Component Breakdown', fontweight='bold', fontsize=12)
    ax2.legend(loc='best', fontsize=8)
    ax2.grid(True, alpha=0.2)
    format_axis(ax2)

    # 3. Borrowed USDT0 Over Time
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.fill_between(time_days, 0, borrowed, alpha=0.6, color='#ff6b6b')
    ax3.plot(time_days, borrowed, linewidth=2, color='#ff4757', label='Borrowed USDT0')
    ax3.set_xlabel('Days')
    ax3.set_ylabel('USDT0')
    ax3.set_title('Borrowed USDT0 Position', fontweight='bold', fontsize=12)
    ax3.legend(loc='best')
    ax3.grid(True, alpha=0.2)
    format_axis(ax3)

    # 4. LTV Ratio
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.plot(time_days, ltv, linewidth=2, color='#ffa502', label='LTV %')

    # Add risk threshold line
    max_ltv = 80  # From max_borrow_multiple = 0.8
    ax4.axhline(y=max_ltv, color='#ff4757', linestyle='--',
                linewidth=2, alpha=0.7, label=f'Max LTV ({max_ltv}%)')
    ax4.fill_between(time_days, 0, ltv,
                     where=np.array(ltv) < max_ltv,
                     alpha=0.2, color='#00ff88', label='Safe')
    ax4.fill_between(time_days, 0, ltv,
                     where=np.array(ltv) >= max_ltv,
                     alpha=0.3, color='#ff4757', label='At Risk')

    ax4.set_xlabel('Days')
    ax4.set_ylabel('LTV %')
    ax4.set_title('Loan-to-Value Ratio', fontweight='bold', fontsize=12)
    ax4.legend(loc='best')
    ax4.grid(True, alpha=0.2)
    format_axis(ax4)

    # 5. Individual P&L Components Over Time
    ax5 = fig.add_subplot(gs[2, 0])
    ax5.plot(time_days, fees, linewidth=2, label='Fees', color='#4ecdc4')
    ax5.plot(time_days, underlying_yield, linewidth=2, label='Underlying Yield', color='#95e1d3')
    ax5.plot(time_days, rehyp_yield, linewidth=2, label='Rehyp Yield', color='#f38181')
    ax5.plot(time_days, borrow_cost, linewidth=2, label='Borrow Cost', color='#aa4465')
    ax5.plot(time_days, ops_cost, linewidth=2, label='Ops Cost', color='#662549')
    ax5.axhline(y=0, color='white', linestyle='-', alpha=0.3)
    ax5.set_xlabel('Days')
    ax5.set_ylabel('USD (Cumulative)')
    ax5.set_title('P&L Components (Cumulative)', fontweight='bold', fontsize=12)
    ax5.legend(loc='best', fontsize=8)
    ax5.grid(True, alpha=0.2)
    format_axis(ax5)

    # 6. Impermanent Loss
    ax6 = fig.add_subplot(gs[2, 1])
    il_pct = [r.il_percentage for r in results]
    ax6.plot(time_days, il_pct, linewidth=2, color='#ff6348', label='IL %')
    ax6.fill_between(time_days, 0, il_pct,
                     where=np.array(il_pct) < 0,
                     alpha=0.3, color='#ff6348', label='Negative IL')
    ax6.fill_between(time_days, 0, il_pct,
                     where=np.array(il_pct) >= 0,
                     alpha=0.3, color='#00ff88', label='Positive IL')
    ax6.axhline(y=0, color='white', linestyle='-', alpha=0.3)
    ax6.set_xlabel('Days')
    ax6.set_ylabel('IL %')
    ax6.set_title('Impermanent Loss %', fontweight='bold', fontsize=12)
    ax6.legend(loc='best')
    ax6.grid(True, alpha=0.2)
    format_axis(ax6)

    # Main title
    fig.suptitle(
        f'Eulerswap LP Profitability Simulation\n'
        f'Net P&L: ${summary["net_pnl"]:,.0f} | '
        f'Return: {summary["total_return_pct"]:.2f}% | '
        f'APR: {summary["annualized_return_pct"]:.2f}%',
        fontsize=14,
        fontweight='bold',
        y=0.98
    )

    # Save figure
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#1a1a1a')
    plt.close()


def format_axis(ax):
    """Apply consistent formatting to axis."""
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}' if abs(x) >= 1000 else f'${x:.0f}'))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


def generate_sensitivity_heatmap(
    param_name: str,
    param_values: List[float],
    results_matrix: np.ndarray,
    output_path: str,
    metric_name: str = "Net P&L"
):
    """
    Generate sensitivity heatmap for parameter sweeps.

    Args:
        param_name: Name of parameter being varied
        param_values: List of parameter values
        results_matrix: 2D array of results
        output_path: Path to save plot
        metric_name: Name of metric being plotted
    """
    plt.style.use('dark_background')

    fig, ax = plt.subplots(figsize=(10, 8))

    im = ax.imshow(results_matrix, cmap='RdYlGn', aspect='auto')

    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label(metric_name, rotation=270, labelpad=20)

    ax.set_xlabel(param_name)
    ax.set_ylabel('Scenario')
    ax.set_title(f'Sensitivity Analysis: {metric_name} vs {param_name}',
                fontweight='bold', fontsize=12)

    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#1a1a1a')
    plt.close()


def plot_scenario_comparison(
    scenarios: Dict[str, List[StepResult]],
    output_path: str,
    metric: str = "net_pnl"
):
    """
    Compare multiple scenarios on a single plot.

    Args:
        scenarios: Dictionary mapping scenario names to results
        output_path: Path to save plot
        metric: Metric to plot (e.g., 'net_pnl', 'lp_nav')
    """
    plt.style.use('dark_background')

    fig, ax = plt.subplots(figsize=(12, 6))

    colors = ['#4ecdc4', '#ff6b6b', '#ffd93d', '#95e1d3', '#f38181']

    for i, (name, results) in enumerate(scenarios.items()):
        time_days = [r.time_days for r in results]
        values = [getattr(r, metric) for r in results]

        color = colors[i % len(colors)]
        ax.plot(time_days, values, linewidth=2, label=name, color=color)

    ax.set_xlabel('Days')
    ax.set_ylabel(metric.replace('_', ' ').title())
    ax.set_title(f'Scenario Comparison: {metric.replace("_", " ").title()}',
                fontweight='bold', fontsize=12)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.2)
    format_axis(ax)

    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#1a1a1a')
    plt.close()
