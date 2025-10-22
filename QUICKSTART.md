# Eulerswap Simulator - Quick Start Guide

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Basic Usage

### 1. Run Default Simulation
```bash
python3 -m sim.run --config sim/config.yaml
```

### 2. Generate Plots
```bash
python3 -m sim.run --config sim/config.yaml --plot
```

### 3. Export Results
```bash
# CSV format
python3 -m sim.run --config sim/config.yaml --output results.csv

# JSON format
python3 -m sim.run --config sim/config.yaml --output results.json
```

### 4. Complete Run (with plots and export)
```bash
python3 -m sim.run --config sim/config.yaml --plot --output results.csv
```

## Understanding the Output

### Console Summary
The simulator displays:
- **Initial Capital**: Starting position value
- **Final NAV**: Net asset value at end
- **P&L Breakdown**:
  - Fees earned from trading
  - Yields (underlying + rehypothecation)
  - Borrow costs
  - Operational costs
  - Impermanent loss
- **Returns**: Total and annualized
- **Risk Metrics**: Borrowed amount and LTV ratio

### Plot Interpretation

**6 plots are generated:**

1. **LP NAV** - Track your equity over time
   - Green area = profit
   - Red area = loss

2. **P&L Component Breakdown** - See where money comes from/goes
   - Stacked areas show cumulative effects
   - Yellow line = net P&L

3. **Borrowed USDT0** - Monitor debt position
   - Should decrease over time as trades repay debt

4. **LTV Ratio** - Liquidation risk indicator
   - Stay below red line (80% default)
   - Red area = at risk of liquidation

5. **P&L Components** - Individual tracking of each component
   - Useful for identifying dominant factors

6. **Impermanent Loss** - IL percentage over time
   - Negative = unfavorable vs holding
   - Positive = favorable vs holding

## Modifying Parameters

Edit `sim/config.yaml`:

### Increase Profitability
```yaml
amm:
  fee_bps: 30  # Higher fees (0.3%)

yields:
  underlying_yield_apr: 0.08  # Higher base yield
  rehyp_yield_apr: 0.15       # Higher rehyp yield
  borrow_cost_apr: 0.05       # Lower borrow cost

flow:
  deterministic_schedule_bps_of_pool: 30  # More trading volume
```

### Reduce Risk
```yaml
initial_state:
  rehyp_fraction: 0.3  # Lower rehypothecation

risk:
  max_borrow_multiple: 0.6  # Lower max LTV

yields:
  borrow_cost_apr: 0.06  # Lower borrow rate
```

### Longer/Shorter Horizon
```yaml
horizon_days: 365  # 1 year simulation
steps_per_day: 48  # Higher granularity
```

## Common Scenarios

### Scenario 1: High Volume, Low Margin
```yaml
amm:
  fee_bps: 3
flow:
  deterministic_schedule_bps_of_pool: 50
```

### Scenario 2: Low Volume, High Margin
```yaml
amm:
  fee_bps: 100
flow:
  deterministic_schedule_bps_of_pool: 5
```

### Scenario 3: Bull Market (Rising Yields)
```yaml
yields:
  underlying_yield_apr: 0.12
  rehyp_yield_apr: 0.20
  borrow_cost_apr: 0.06
```

### Scenario 4: Bear Market (Rising Borrow Costs)
```yaml
yields:
  underlying_yield_apr: 0.04
  rehyp_yield_apr: 0.08
  borrow_cost_apr: 0.12
```

## Running Tests

```bash
# Note: Tests may fail due to pytest-web3 plugin conflict
# Use direct Python execution to verify:

python3 -m sim.run --config sim/config.yaml --quiet
```

## Interpreting Results

### Positive NAV Growth
✅ Strategy is profitable
- Fees + Yields > Borrow Cost + Ops Cost + IL

### Negative NAV Growth
❌ Strategy is unprofitable
- Review:
  - Is borrow cost too high?
  - Is trading volume too low?
  - Are operational costs justified?

### High LTV (>80%)
⚠️ Liquidation risk
- Solutions:
  - Increase initial USDT0 reserve
  - Reduce plUSD deposit
  - Lower rehyp fraction

### High IL (>10%)
⚠️ Significant rebalancing
- Expected with one-sided flow
- Ensure fees compensate

## Tips for Optimization

1. **Balance Yield vs Risk**
   - Higher rehyp = more yield but more complexity
   - Keep LTV < 60% for safety margin

2. **Fee Selection**
   - Low fees (3-7 bps) for high volume
   - High fees (30-100 bps) for low volume

3. **Capital Efficiency**
   - Start with smaller deposit
   - Scale up if profitable

4. **Monitoring**
   - Export CSV for time-series analysis
   - Use plots to spot trends early

## Troubleshooting

**Error: "No module named 'numpy'"**
```bash
pip install -r requirements.txt
```

**Negative NAV from start**
- Borrow cost likely exceeds yields
- Reduce `borrow_cost_apr` or increase yields

**LTV > 100%**
- Position underwater
- Reduce `deterministic_schedule_bps_of_pool`
- Increase `usdt0_reserve`

**Plots not generating**
```bash
pip install matplotlib
mkdir -p output
```

## Next Steps

1. Run baseline simulation
2. Modify one parameter at a time
3. Compare results
4. Find optimal configuration
5. Implement in production with monitoring

## Support

- GitHub: https://github.com/Figu3/eulerswap-simulator
- Issues: https://github.com/Figu3/eulerswap-simulator/issues
- Documentation: See README.md

---

**Happy Simulating! 🚀**
