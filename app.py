#!/usr/bin/env python3
"""
Streamlit web interface for Eulerswap LP Profitability Simulator.
Deploy to Streamlit Cloud, Railway, or Render (not Vercel - Python not supported).
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

from sim.core import SimulationEngine, SimulationParams, PoolState

# Page config
st.set_page_config(
    page_title="Eulerswap Rehypothecation Simulator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1f2937;
        padding: 10px;
        border-radius: 5px;
    }
    h1 {
        color: #00ff88;
    }
    h2, h3 {
        color: #4ecdc4;
    }
</style>
""", unsafe_allow_html=True)


def run_simulation(params_dict):
    """Run simulation with given parameters."""

    # Create params
    params = SimulationParams(
        horizon_days=params_dict['horizon_days'],
        steps_per_day=params_dict['steps_per_day'],
        seed=42,
        amm_type="constant_product",
        fee_bps=params_dict['fee_bps'],
        underlying_yield_apr=params_dict['underlying_yield_apr'],
        rehyp_yield_apr=params_dict['rehyp_yield_apr'],
        borrow_cost_apr=params_dict['borrow_cost_apr'],
        ops_cost_usd_per_day=params_dict['ops_cost_usd_per_day'],
        flow_model="deterministic",
        deterministic_schedule_bps=params_dict['flow_bps'],
        max_borrow_multiple=0.8,
        peg_deviation_std_bps=5,
        mark_plusd_price=1.0,
        mark_usdt0_price=1.0
    )

    # Create initial state
    initial_state = PoolState(
        plusd_reserve=params_dict['plusd_reserve'],
        usdt0_reserve=params_dict['usdt0_reserve'],
        trevee_plusd=params_dict['trevee_deposit'],
        trevee_usdt0=0.0,
        rehypothecated_plusd=params_dict['trevee_deposit'] * params_dict['rehyp_fraction'],
        borrowed_usdt0=params_dict['usdt0_reserve'],
        fee_accruals=0.0,
        underlying_yield_accrued=0.0,
        rehyp_yield_accrued=0.0,
        borrow_cost_accrued=0.0,
        ops_cost_accrued=0.0,
        initial_trevee_plusd=params_dict['trevee_deposit'],
        initial_trevee_usdt0=0.0,
        step=0
    )

    # Run simulation
    engine = SimulationEngine(params, initial_state)
    results = engine.run()
    summary = engine.get_summary()

    return results, summary


def plot_results(results, summary):
    """Create interactive Plotly charts."""

    # Extract data
    time_days = [r.time_days for r in results]
    nav = [r.lp_nav for r in results]
    fees = [r.total_fees for r in results]
    yields_total = [r.total_underlying_yield + r.total_rehyp_yield for r in results]
    borrow_cost = [-r.total_borrow_cost for r in results]
    ops_cost = [-r.total_ops_cost for r in results]
    borrowed = [r.borrowed_usdt0 for r in results]
    ltv = [r.ltv * 100 for r in results]
    net_pnl = [r.net_pnl for r in results]

    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('LP NAV Over Time', 'P&L Components', 'Borrowed USDT0', 'LTV Ratio'),
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )

    # 1. NAV
    fig.add_trace(
        go.Scatter(x=time_days, y=nav, name='NAV', line=dict(color='#00ff88', width=2)),
        row=1, col=1
    )
    fig.add_hline(y=summary['initial_capital'], line_dash="dash", line_color="#ff6b6b",
                  annotation_text="Initial Capital", row=1, col=1)

    # 2. P&L Components
    fig.add_trace(
        go.Scatter(x=time_days, y=fees, name='Fees', fill='tonexty',
                  fillcolor='rgba(78, 205, 196, 0.5)', line=dict(color='#4ecdc4')),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(x=time_days, y=yields_total, name='Yields', fill='tonexty',
                  fillcolor='rgba(149, 225, 211, 0.5)', line=dict(color='#95e1d3')),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(x=time_days, y=borrow_cost, name='Borrow Cost', fill='tonexty',
                  fillcolor='rgba(170, 68, 101, 0.5)', line=dict(color='#aa4465')),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(x=time_days, y=net_pnl, name='Net P&L',
                  line=dict(color='#ffd93d', width=3)),
        row=1, col=2
    )

    # 3. Borrowed
    fig.add_trace(
        go.Scatter(x=time_days, y=borrowed, name='Borrowed', fill='tozeroy',
                  fillcolor='rgba(255, 107, 107, 0.3)', line=dict(color='#ff6b6b')),
        row=2, col=1
    )

    # 4. LTV
    fig.add_trace(
        go.Scatter(x=time_days, y=ltv, name='LTV %', line=dict(color='#ffa502', width=2)),
        row=2, col=2
    )
    fig.add_hline(y=80, line_dash="dash", line_color="#ff4757",
                  annotation_text="Max LTV (80%)", row=2, col=2)

    # Update layout
    fig.update_layout(
        height=700,
        showlegend=True,
        template="plotly_dark",
        paper_bgcolor='#0e1117',
        plot_bgcolor='#1f2937',
        font=dict(color='white'),
        hovermode='x unified'
    )

    fig.update_xaxes(title_text="Days", row=2, col=1)
    fig.update_xaxes(title_text="Days", row=2, col=2)
    fig.update_yaxes(title_text="USD", row=1, col=1)
    fig.update_yaxes(title_text="USD", row=1, col=2)
    fig.update_yaxes(title_text="USDT0", row=2, col=1)
    fig.update_yaxes(title_text="%", row=2, col=2)

    return fig


def main():
    """Main Streamlit app."""

    # Title
    st.title("📊 Eulerswap Rehypothecation Profitability Simulator")
    st.markdown("### One-sided liquidity provision with rehypothecation yield analysis (plUSD only)")

    # Sidebar - Parameters
    st.sidebar.header("⚙️ Simulation Parameters")

    # Scenario presets
    scenario = st.sidebar.selectbox(
        "Preset Scenarios",
        ["Custom", "Default", "Profitable", "High Volume", "Optimized"]
    )

    # Load preset values
    if scenario == "Default":
        preset = {
            'horizon_days': 180, 'fee_bps': 7, 'flow_bps': 20,
            'plusd_reserve': 5_000_000, 'usdt0_reserve': 5_000_000,
            'trevee_deposit': 1_000_000, 'rehyp_fraction': 0.6,
            'underlying_yield_apr': 0.06, 'rehyp_yield_apr': 0.12,
            'borrow_cost_apr': 0.08, 'ops_cost_usd_per_day': 150
        }
    elif scenario == "Profitable":
        preset = {
            'horizon_days': 90, 'fee_bps': 30, 'flow_bps': 25,
            'plusd_reserve': 5_000_000, 'usdt0_reserve': 5_000_000,
            'trevee_deposit': 1_000_000, 'rehyp_fraction': 0.5,
            'underlying_yield_apr': 0.08, 'rehyp_yield_apr': 0.15,
            'borrow_cost_apr': 0.06, 'ops_cost_usd_per_day': 100
        }
    elif scenario == "High Volume":
        preset = {
            'horizon_days': 30, 'fee_bps': 7, 'flow_bps': 50,
            'plusd_reserve': 10_000_000, 'usdt0_reserve': 10_000_000,
            'trevee_deposit': 2_000_000, 'rehyp_fraction': 0.6,
            'underlying_yield_apr': 0.06, 'rehyp_yield_apr': 0.12,
            'borrow_cost_apr': 0.07, 'ops_cost_usd_per_day': 100
        }
    elif scenario == "Optimized":
        preset = {
            'horizon_days': 90, 'fee_bps': 50, 'flow_bps': 40,
            'plusd_reserve': 5_000_000, 'usdt0_reserve': 5_000_000,
            'trevee_deposit': 500_000, 'rehyp_fraction': 0.7,
            'underlying_yield_apr': 0.10, 'rehyp_yield_apr': 0.18,
            'borrow_cost_apr': 0.05, 'ops_cost_usd_per_day': 50
        }
    else:
        preset = {
            'horizon_days': 90, 'fee_bps': 7, 'flow_bps': 20,
            'plusd_reserve': 5_000_000, 'usdt0_reserve': 5_000_000,
            'trevee_deposit': 1_000_000, 'rehyp_fraction': 0.6,
            'underlying_yield_apr': 0.06, 'rehyp_yield_apr': 0.12,
            'borrow_cost_apr': 0.08, 'ops_cost_usd_per_day': 150
        }

    st.sidebar.markdown("---")
    st.sidebar.subheader("Time")
    horizon_days = st.sidebar.slider("Horizon (days)", 7, 365, preset['horizon_days'])
    steps_per_day = st.sidebar.slider("Steps per day", 1, 48, 24)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Pool & LP")
    plusd_reserve = st.sidebar.number_input("plUSD Reserve", 100_000, 50_000_000, preset['plusd_reserve'], 100_000)
    usdt0_reserve = st.sidebar.number_input("USDT0 Reserve", 100_000, 50_000_000, preset['usdt0_reserve'], 100_000)
    trevee_deposit = st.sidebar.number_input("Trevee Deposit (plUSD)", 100_000, 10_000_000, preset['trevee_deposit'], 100_000)

    st.sidebar.markdown("---")
    st.sidebar.subheader("AMM")
    fee_bps = st.sidebar.slider("Fee (bps)", 1, 100, preset['fee_bps'])
    flow_bps = st.sidebar.slider("Daily Flow (bps of pool)", 1, 100, preset['flow_bps'])

    st.sidebar.markdown("---")
    st.sidebar.subheader("Yields & Costs")
    underlying_yield_apr = st.sidebar.slider("Underlying Yield APR", 0.0, 0.25, preset['underlying_yield_apr'], 0.01)
    rehyp_yield_apr = st.sidebar.slider("Rehyp Yield APR", 0.0, 0.30, preset['rehyp_yield_apr'], 0.01)
    rehyp_fraction = st.sidebar.slider("Rehyp Fraction", 0.0, 1.0, preset['rehyp_fraction'], 0.05)
    borrow_cost_apr = st.sidebar.slider("Borrow Cost APR", 0.0, 0.20, preset['borrow_cost_apr'], 0.01)
    ops_cost_usd_per_day = st.sidebar.number_input("Ops Cost ($/day)", 0, 1000, preset['ops_cost_usd_per_day'], 10)

    # Run simulation button
    if st.sidebar.button("🚀 Run Simulation", type="primary"):
        with st.spinner("Running simulation..."):
            params_dict = {
                'horizon_days': horizon_days,
                'steps_per_day': steps_per_day,
                'plusd_reserve': plusd_reserve,
                'usdt0_reserve': usdt0_reserve,
                'trevee_deposit': trevee_deposit,
                'rehyp_fraction': rehyp_fraction,
                'fee_bps': fee_bps,
                'flow_bps': flow_bps,
                'underlying_yield_apr': underlying_yield_apr,
                'rehyp_yield_apr': rehyp_yield_apr,
                'borrow_cost_apr': borrow_cost_apr,
                'ops_cost_usd_per_day': ops_cost_usd_per_day
            }

            results, summary = run_simulation(params_dict)

            # Store in session state
            st.session_state['results'] = results
            st.session_state['summary'] = summary

    # Display results
    if 'summary' in st.session_state:
        summary = st.session_state['summary']
        results = st.session_state['results']

        # Metrics
        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Net P&L", f"${summary['net_pnl']:,.0f}")
        with col2:
            st.metric("Total Return", f"{summary['total_return_pct']:.2f}%")
        with col3:
            st.metric("Annual Return", f"{summary['annualized_return_pct']:.2f}%",
                     delta=f"{summary['annualized_return_pct']:.2f}%")
        with col4:
            st.metric("Final LTV", f"{summary['final_ltv']:.1%}",
                     delta="Risk" if summary['final_ltv'] > 0.8 else "Safe",
                     delta_color="inverse")
        with col5:
            st.metric("Max Drawdown", f"{summary['max_drawdown']:.2f}%")

        # P&L Breakdown
        st.markdown("---")
        st.subheader("💰 P&L Breakdown")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📈 Total Fees", f"${summary['total_fees']:,.0f}")
            st.metric("📊 Total Yields", f"${summary['total_yields']:,.0f}")
        with col2:
            st.metric("📉 Borrow Cost", f"-${summary['total_borrow_cost']:,.0f}")
            st.metric("💸 Ops Cost", f"-${summary['total_ops_cost']:,.0f}")
        with col3:
            st.metric("🔄 IL", f"{summary['final_il_pct']:.2f}%")
            st.metric("💼 Final NAV", f"${summary['final_nav']:,.0f}")

        # Charts
        st.markdown("---")
        st.subheader("📈 Performance Charts")
        fig = plot_results(results, summary)
        st.plotly_chart(fig, use_container_width=True)

        # Data table
        st.markdown("---")
        st.subheader("📋 Detailed Results")

        df = pd.DataFrame([
            {
                'Day': r.time_days,
                'NAV': r.lp_nav,
                'Net P&L': r.net_pnl,
                'Fees': r.total_fees,
                'Yields': r.total_underlying_yield + r.total_rehyp_yield,
                'Borrow Cost': -r.total_borrow_cost,
                'Borrowed USDT0': r.borrowed_usdt0,
                'LTV %': r.ltv * 100,
            }
            for r in results[::24]  # Daily snapshots
        ])

        st.dataframe(df.style.format({
            'Day': '{:.0f}',
            'NAV': '${:,.0f}',
            'Net P&L': '${:,.0f}',
            'Fees': '${:,.0f}',
            'Yields': '${:,.0f}',
            'Borrow Cost': '${:,.0f}',
            'Borrowed USDT0': '${:,.0f}',
            'LTV %': '{:.1f}%',
        }), use_container_width=True)

        # Download
        csv = df.to_csv(index=False)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name="eulerswap_simulation.csv",
            mime="text/csv"
        )

    else:
        # Welcome message
        st.info("👈 Configure parameters in the sidebar and click **Run Simulation** to get started!")

        st.markdown("---")
        st.markdown("""
        ### How It Works

        This simulator models LP profitability for **one-sided liquidity provision** where:
        - Trevee deposits **plUSD only**
        - USDT0 is **borrowed** to balance the pool
        - All trades flow **plUSD → USDT0**

        #### P&L Components
        - ✅ **Fees**: Trading fees earned (proportional to LP share)
        - ✅ **Underlying Yield**: Base yield on plUSD holdings
        - ✅ **Rehyp Yield**: Additional yield from rehypothecated assets
        - ❌ **Borrow Cost**: Interest on borrowed USDT0
        - ❌ **Ops Cost**: Daily operational expenses
        - ⚖️ **IL**: Impermanent loss vs holding

        #### Risk Metrics
        - **LTV Ratio**: Borrowed USDT0 / Collateral plUSD
        - **Max LTV**: 80% (liquidation threshold)

        ### Quick Start
        1. Select a preset scenario or configure custom parameters
        2. Click "Run Simulation"
        3. Analyze results and download data
        """)


if __name__ == "__main__":
    main()
