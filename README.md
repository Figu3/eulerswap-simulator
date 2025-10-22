# Eulerswap LP Profitability Simulator

A Python-based simulator for analyzing LP profitability when Trevee provides one-sided liquidity (plUSD only) in a constant-product AMM, with all trade flow being **plUSD → USDT0**.

## Overview

This simulator models the economics of:
- **One-sided LP provision** (plUSD deposit, USDT0 borrowed)
- **Directional trade flow** (all swaps are plUSD → USDT0)
- **Multiple yield sources**: underlying yield, rehypothecation yield
- **Borrowing costs** for USDT0
- **Operational costs**
- **Impermanent loss** tracking
- **Liquidation risk** monitoring

## Model Logic

### Pool Mechanics
- **AMM Type**: Constant-product (x · y = k)
- **Fee Model**: Configurable basis points per trade (default: 7 bps)
- **Reserves**: Two-asset pool (plUSD, USDT0)

### Trevee LP Position
1. **Initial Setup**: Trevee deposits plUSD only
2. **USDT0 Provision**: Borrowed to balance pool liquidity
3. **Rehypothecation**: Fraction of plUSD (default 60%) is rehypothecated for additional yield
4. **Trade Flow**: All trades are plUSD → USDT0, gradually reducing borrowed position

### P&L Components

| Component | Formula | Description |
|-----------|---------|-------------|
| **Fees** | Σ(volume × fee_bps) | Trading fees earned proportional to LP share |
| **Underlying Yield** | plUSD_balance × underlying_yield_apr | Base yield on plUSD holdings |
| **Rehyp Yield** | rehyp_fraction × plUSD_balance × rehyp_yield_apr | Additional yield from rehypothecated assets |
| **Borrow Cost** | borrowed_USDT0 × borrow_cost_apr | Interest on borrowed USDT0 |
| **IL** | vs holding plUSD | Impermanent loss from AMM rebalancing |
| **Ops Cost** | ops_cost_usd_per_day × t | Fixed operational expenses |
| **Net P&L** | fees + yields - borrow_cost - IL - ops_cost | Total profitability |

### Simulation Steps

Each time step executes:
1. Generate trade flow (deterministic or stochastic)
2. Execute swap (plUSD → USDT0)
3. Calculate and accrue LP fees
4. Accrue yields (underlying + rehyp)
5. Accrue borrow costs
6. Update LP position (USDT0 received reduces debt)
7. Calculate NAV and P&L
8. Check liquidation risk (LTV ratio)

## Installation

```bash
# Clone repository
git clone <repo-url>
cd eulerswap-simulator

# Install dependencies
pip install -r requirements.txt
```

### Requirements
```
numpy>=1.24.0
matplotlib>=3.7.0
pyyaml>=6.0
pytest>=7.3.0
```

## Quick Start

### 1. Basic Simulation

```bash
python -m sim.run --config sim/config.yaml
```

### 2. With Plots

```bash
python -m sim.run --config sim/config.yaml --plot
```

### 3. Export Results

```bash
# Export to CSV
python -m sim.run --config sim/config.yaml --output results.csv

# Export to JSON
python -m sim.run --config sim/config.yaml --output results.json
```

### 4. Custom Configuration

Edit `sim/config.yaml`:

```yaml
horizon_days: 180          # Simulation duration
steps_per_day: 24          # Time granularity

amm:
  fee_bps: 7               # 0.07% trading fee

initial_state:
  plusd_reserve: 5_000_000
  usdt0_reserve: 5_000_000
  trevee_deposit_plusd: 1_000_000
  rehyp_fraction: 0.6      # 60% rehypothecated

yields:
  underlying_yield_apr: 0.06   # 6% base yield
  rehyp_yield_apr: 0.12        # 12% rehyp yield
  borrow_cost_apr: 0.08        # 8% borrow cost

flow:
  model: "deterministic"
  deterministic_schedule_bps_of_pool: 20  # 0.2% daily flow
```

## Configuration Reference

### Time Parameters
- `horizon_days`: Total simulation duration
- `steps_per_day`: Number of steps per day (higher = more granular)
- `seed`: Random seed for reproducibility

### AMM Parameters
- `amm.type`: AMM curve type (currently "constant_product")
- `amm.fee_bps`: Trading fee in basis points

### Initial State
- `plusd_reserve`: Initial plUSD in pool
- `usdt0_reserve`: Initial USDT0 in pool
- `trevee_deposit_plusd`: Trevee's plUSD deposit
- `rehyp_fraction`: Fraction of plUSD to rehypothecate (0.0 to 1.0)

### Yield & Cost Parameters
- `underlying_yield_apr`: Annual yield on plUSD (decimal, e.g., 0.06 = 6%)
- `rehyp_yield_apr`: Annual yield on rehypothecated plUSD
- `borrow_cost_apr`: Annual interest on borrowed USDT0
- `ops_cost_usd_per_day`: Daily operational costs

### Flow Model
- `flow.model`: "deterministic" or "stochastic"
- `deterministic_schedule_bps_of_pool`: Daily flow as % of pool (deterministic)
- `stochastic.mu_daily`: Mean daily drift (stochastic)
- `stochastic.sigma_daily`: Daily volatility (stochastic)

### Risk Parameters
- `max_borrow_multiple`: Maximum LTV ratio before liquidation
- `peg_deviation_std_bps`: Standard deviation of price noise (optional)

### Reporting
- `mark_to_market_price_plusd`: MTM price for plUSD (default: 1.0)
- `mark_to_market_price_usdt0`: MTM price for USDT0 (default: 1.0)

## Output

### Console Summary
```
============================================================
SIMULATION SUMMARY
============================================================

Time Horizon: 180 days
Initial Capital: $1,000,000.00
Final NAV: $1,089,456.23

------------------------------------------------------------
P&L BREAKDOWN
------------------------------------------------------------
Total Fees Earned: $42,350.12
Total Yields: $124,678.90
Total Borrow Cost: -$98,234.56
Total Ops Cost: -$27,000.00
Impermanent Loss: -2.34%
------------------------------------------------------------
Net P&L: $89,456.23

------------------------------------------------------------
RETURNS
------------------------------------------------------------
Total Return: 8.95%
Annualized Return: 18.23%
Max Drawdown: 3.45%

------------------------------------------------------------
RISK METRICS
------------------------------------------------------------
Final Borrowed USDT0: $3,456,789.01
Final LTV: 34.57%
```

### Plots

Generated plots include:
1. **LP NAV Over Time**: Shows equity growth/drawdown
2. **P&L Component Breakdown**: Stacked area chart of all P&L sources
3. **Borrowed USDT0**: Debt position over time
4. **LTV Ratio**: Liquidation risk monitoring
5. **P&L Components (Cumulative)**: Individual component tracking
6. **Impermanent Loss**: IL percentage over time

### CSV/JSON Export

Exported data includes per-step metrics:
- Time and step number
- Reserve balances
- LP position (plUSD, USDT0)
- Borrowed amounts
- Trade flow and output
- Fee and yield accruals
- NAV and P&L
- Risk metrics (LTV)

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_models.py -v

# Run with coverage
pytest tests/ --cov=sim --cov-report=html
```

### Test Coverage

Tests verify:
- ✓ AMM swap mechanics (constant product, fees)
- ✓ Continuous compounding accruals
- ✓ Impermanent loss calculations
- ✓ Liquidation risk assessment
- ✓ Zero-fee/zero-flow scenarios (yields only)
- ✓ Fee impact on profitability
- ✓ Borrow cost effects

## Extending the Simulator

### Adding New AMM Curves

1. Implement new swap function in `sim/models.py`:
```python
def swap_stableswap(x_reserve, y_reserve, x_in, fee_bps, A):
    """StableSwap invariant: A * sum(x_i) + product(x_i) = constant"""
    # Implementation here
    pass
```

2. Update `execute_swap()` in `sim/core.py`:
```python
if self.params.amm_type == "stableswap":
    usdt0_out, new_plusd, new_usdt0 = swap_stableswap(...)
```

3. Add `A` parameter to config:
```yaml
amm:
  type: "stableswap"
  fee_bps: 4
  amplification: 100
```

### Adding New Flow Models

1. Extend `generate_trade_flow()` in `sim/core.py`:
```python
elif self.params.flow_model == "seasonal":
    # Implement seasonal patterns
    day_of_year = (step / self.params.steps_per_day) % 365
    seasonal_factor = 1 + 0.3 * math.sin(2 * math.pi * day_of_year / 365)
    return base_flow * seasonal_factor
```

2. Add parameters to `SimulationParams`:
```python
@dataclass
class SimulationParams:
    # ...
    seasonal_amplitude: float = 0.3
    seasonal_period_days: int = 365
```

### Custom Metrics

Add new metrics to `StepResult` dataclass in `sim/core.py`:
```python
@dataclass
class StepResult:
    # Existing fields...
    sharpe_ratio: float = 0.0
    volatility: float = 0.0
```

Then calculate in `step_simulation()`:
```python
result = StepResult(
    # ...
    sharpe_ratio=self._calculate_sharpe(),
    volatility=self._calculate_volatility()
)
```

## Limitations

### Current Assumptions
1. **Constant prices**: Assumes plUSD and USDT0 maintain 1:1 peg
2. **No cross-asset volatility**: Doesn't model depegging scenarios
3. **Unidirectional flow**: All trades are plUSD → USDT0
4. **No liquidity depth**: Price impact calculated but no order book
5. **No external arbitrage**: LP is the only liquidity provider
6. **Continuous time**: Uses discrete time steps with continuous compounding approximation

### Known Edge Cases
- **High trade volume**: Can drain USDT0 reserve, causing slippage
- **Liquidation**: Simulator doesn't force-close positions at max LTV
- **Negative IL**: Can occur when receiving more assets than HODL
- **Rehyp fraction > 1**: Not validated, would be over-leveraged

## Use Cases

### 1. Profitability Analysis
Determine if LP strategy is viable given:
- Expected trade volume
- Yield rates
- Borrowing costs

### 2. Parameter Optimization
Find optimal:
- Fee tier (3, 7, 30 bps)
- Rehypothecation fraction
- Initial capital allocation

### 3. Risk Assessment
Evaluate:
- Maximum drawdown scenarios
- Liquidation risk under stress
- Sensitivity to borrow cost changes

### 4. Scenario Planning
Model different market conditions:
- High/low trading volume
- Rate environment changes
- Operational cost variations

## Example Scenarios

### Conservative (Low Risk)
```yaml
initial_state:
  trevee_deposit_plusd: 500_000
  rehyp_fraction: 0.3        # Low rehyp

yields:
  borrow_cost_apr: 0.06      # Low borrow cost

flow:
  deterministic_schedule_bps_of_pool: 10  # Moderate flow
```

### Aggressive (High Yield)
```yaml
initial_state:
  trevee_deposit_plusd: 2_000_000
  rehyp_fraction: 0.8        # High rehyp

yields:
  rehyp_yield_apr: 0.18      # High rehyp yield
  borrow_cost_apr: 0.10      # Higher borrow cost

flow:
  deterministic_schedule_bps_of_pool: 30  # High flow
```

## Troubleshooting

### Negative NAV
**Cause**: Borrow costs exceed fee + yield income
**Solution**: Reduce `borrow_cost_apr` or increase `fee_bps`

### Liquidation Risk
**Cause**: LTV ratio exceeds `max_borrow_multiple`
**Solution**: Increase initial `usdt0_reserve` or reduce trade flow

### Low Fees
**Cause**: Insufficient trade volume or low LP share
**Solution**: Increase `deterministic_schedule_bps` or `trevee_deposit_plusd`

### High IL
**Cause**: Large reserve imbalances from one-sided flow
**Solution**: Expected behavior - monitor that fees + yields exceed IL

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure `pytest -q` passes
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## References

- [Uniswap V2 Whitepaper](https://uniswap.org/whitepaper.pdf) - Constant product AMM
- [Impermanent Loss Calculator](https://dailydefi.org/tools/impermanent-loss-calculator/)
- [Continuous Compounding](https://en.wikipedia.org/wiki/Compound_interest#Continuous_compounding)

## Contact

For questions or support, please open an issue on GitHub.

---

**Built for Trevee Earn** | Version 0.1.0
