# Eulerswap Simulator - Scenario Analysis Guide

## Overview

This simulator is a **pure mathematical model** - no blockchain data fetching required. It models LP profitability based on configurable parameters representing market conditions.

## What This Tool Does

**Models one-sided liquidity provision economics:**
- Trevee deposits only plUSD
- USDT0 is borrowed to balance the pool
- All trades flow plUSD → USDT0
- Calculates: fees earned, yields, borrow costs, IL, net P&L

**This is NOT an on-chain data tool** - it's a forward-looking profitability calculator.

## Pre-configured Scenarios

### 1. Default (`config.yaml`)
**Market Conditions:** Standard rates, moderate volume
```yaml
Fee: 7 bps | Flow: 20 bps/day | Horizon: 180 days
Yields: 6% underlying + 12% rehyp
Borrow Cost: 8%
```

**Results:**
- Net P&L: -$45,534
- Annual Return: -9.23%
- **Verdict:** ❌ Unprofitable - borrow costs exceed income

**Why it fails:** Borrow cost (8%) > weighted yields (7.2%), and fees are minimal

---

### 2. Profitable (`config_profitable.yaml`)
**Market Conditions:** Higher fees, lower borrow cost
```yaml
Fee: 30 bps | Flow: 25 bps/day | Horizon: 90 days
Yields: 8% underlying + 15% rehyp
Borrow Cost: 6%
```

**Results:**
- Net P&L: +$7,418
- Annual Return: +3.01%
- **Verdict:** ✅ Slightly profitable

**Key insight:** Lower borrow cost + higher fees make it work

---

### 3. High Volume (`config_high_volume.yaml`)
**Market Conditions:** Heavy trading, larger pool
```yaml
Fee: 7 bps | Flow: 50 bps/day | Horizon: 30 days
Yields: 6% underlying + 12% rehyp
Borrow Cost: 7%
```

**Results:**
- Net P&L: -$9,735
- Annual Return: -5.92%
- **Verdict:** ❌ Still unprofitable despite high volume

**Key insight:** High LTV (381%) creates too much debt interest

---

### 4. Optimized (`config_optimized.yaml`)
**Market Conditions:** Best case - high fees, low borrow cost, aggressive rehyp
```yaml
Fee: 50 bps | Flow: 40 bps/day | Horizon: 90 days
Yields: 10% underlying + 18% rehyp
Borrow Cost: 5%
Deposit: $500k (smaller = less debt)
```

**Results:**
- Net P&L: +$6,329
- Annual Return: +5.13%
- **Verdict:** ✅ Best performance

**Key insight:** Smaller deposit + higher fees + aggressive rehyp works

---

## Running Scenario Comparison

```bash
python3 examples/compare_scenarios.py
```

This generates a side-by-side comparison table showing which scenario is best for:
- Highest return
- Most fees
- Lowest risk (LTV)

## Key Findings

### ✅ Profitable Conditions
Strategy is profitable when:
1. **Borrow cost < weighted yield** (e.g., 5% < 14%)
2. **High trading volume** (40+ bps/day)
3. **High fees** (30-50 bps)
4. **Aggressive rehypothecation** (60-70%)
5. **Smaller deposits** (reduces borrowed USDT0)

### ❌ Unprofitable Conditions
Strategy fails when:
1. **Borrow cost > yields** (e.g., 8% > 7%)
2. **Low trading volume** (< 20 bps/day)
3. **Low fees** (7 bps or less)
4. **Large deposits** (more borrowed USDT0)

## Understanding the Metrics

### Net P&L Components

| Component | Formula | Impact |
|-----------|---------|--------|
| **Fees** | volume × fee_bps × lp_share | ⬆️ Higher with more volume/fees |
| **Underlying Yield** | plusd × underlying_apr | ⬆️ Grows with deposit size |
| **Rehyp Yield** | rehyp_fraction × plusd × rehyp_apr | ⬆️ Boost with aggressive rehyp |
| **Borrow Cost** | borrowed_usdt0 × borrow_apr | ⬇️ Kills profit if too high |
| **Ops Cost** | daily_cost × days | ⬇️ Fixed drain |
| **IL** | Pool rebalancing vs HODL | ⬇️ Usually negative with one-sided flow |

### LTV (Loan-to-Value) Ratio
```
LTV = borrowed_usdt0 / collateral_plusd
```

- **< 60%**: Safe ✅
- **60-80%**: Warning ⚠️
- **> 80%**: Liquidation risk 🚨

## Creating Custom Scenarios

### Example: Bull Market (Rising Yields)
```yaml
# config_bull.yaml
yields:
  underlying_yield_apr: 0.15  # 15% yields
  rehyp_yield_apr: 0.25       # 25% rehyp
  borrow_cost_apr: 0.06       # Low borrow cost

flow:
  deterministic_schedule_bps_of_pool: 30  # Good volume
```

### Example: Bear Market (High Borrow Costs)
```yaml
# config_bear.yaml
yields:
  underlying_yield_apr: 0.04  # Low yields
  rehyp_yield_apr: 0.08
  borrow_cost_apr: 0.12       # High borrow cost

flow:
  deterministic_schedule_bps_of_pool: 10  # Low volume
```

### Example: DeFi Summer (Everything Pumps)
```yaml
# config_defi_summer.yaml
amm:
  fee_bps: 100  # High fees

yields:
  underlying_yield_apr: 0.20
  rehyp_yield_apr: 0.35
  borrow_cost_apr: 0.05

flow:
  deterministic_schedule_bps_of_pool: 60  # Heavy volume
```

## Sensitivity Analysis

### Most Impactful Parameters (Ranked)

1. **borrow_cost_apr** ⭐⭐⭐⭐⭐
   - Single biggest factor
   - 1% change = significant P&L swing

2. **rehyp_yield_apr** ⭐⭐⭐⭐
   - Major profit driver
   - Combined with rehyp_fraction

3. **fee_bps** ⭐⭐⭐⭐
   - Critical for high-volume scenarios
   - 7 → 50 bps = 7x fee income

4. **trevee_deposit_plusd** ⭐⭐⭐
   - Larger deposit = more borrowed USDT0
   - Paradoxically, smaller can be better

5. **deterministic_schedule_bps** ⭐⭐⭐
   - More volume = more fees
   - But also more IL

6. **ops_cost_usd_per_day** ⭐⭐
   - Linear impact
   - $150/day = -$27k over 180 days

## Strategy Recommendations

### Conservative Strategy
```yaml
trevee_deposit_plusd: 250_000     # Small position
rehyp_fraction: 0.3               # Low rehyp
fee_bps: 30                       # Moderate fees
borrow_cost_apr: 0.05             # Require low borrow environment
```

**Target:** 3-5% APR, LTV < 50%

### Aggressive Strategy
```yaml
trevee_deposit_plusd: 500_000     # Medium position
rehyp_fraction: 0.7               # High rehyp
fee_bps: 50                       # Premium fees
borrow_cost_apr: 0.06             # Accept moderate borrow cost
```

**Target:** 5-8% APR, LTV < 70%

### Degen Strategy
```yaml
trevee_deposit_plusd: 1_000_000   # Large position
rehyp_fraction: 0.8               # Maximum rehyp
fee_bps: 100                      # Extreme fees
borrow_cost_apr: 0.08             # Any borrow cost
```

**Target:** 10%+ APR or -20% loss, LTV can exceed 100% 💀

## Running Custom Scenarios

```bash
# 1. Copy a config
cp sim/config.yaml sim/config_custom.yaml

# 2. Edit parameters
nano sim/config_custom.yaml

# 3. Run simulation
python3 -m sim.run --config sim/config_custom.yaml --plot

# 4. Export for analysis
python3 -m sim.run --config sim/config_custom.yaml --output custom_results.csv
```

## Interpreting Results

### Positive NAV Growth
✅ **Strategy is viable**
- Implement with monitoring
- Watch LTV ratio
- Adjust if markets change

### Flat NAV
⚠️ **Break-even**
- Marginal strategy
- Small parameter changes make/break it
- Consider opportunity cost

### Negative NAV Growth
❌ **Strategy fails**
- Do NOT implement
- Need better parameters
- Or different market conditions

## Real-World Application

### Step 1: Model Current Market
```yaml
# Use actual market rates
underlying_yield_apr: 0.055  # Current plUSD yield
borrow_cost_apr: 0.075       # Current USDT0 borrow rate
```

### Step 2: Estimate Volume
```yaml
# Based on expected trade flow
deterministic_schedule_bps_of_pool: 15  # Conservative estimate
```

### Step 3: Run Simulation
```bash
python3 -m sim.run --config sim/config_realistic.yaml --plot
```

### Step 4: Analyze Scenarios
```python
# Vary key parameters
for borrow_cost in [0.05, 0.06, 0.07, 0.08, 0.09]:
    # Update config and run
    # Compare results
```

### Step 5: Decision
- If all scenarios show negative returns → Don't deploy
- If profitable under reasonable assumptions → Deploy with monitoring
- If marginal → Need better terms or wait for better market

## Limitations to Remember

1. **No price volatility** - Assumes 1:1 peg holds
2. **No depeg scenarios** - Doesn't model plUSD breaking peg
3. **Unidirectional flow** - All trades one way (plUSD → USDT0)
4. **No arbitrage** - Doesn't model external arb bots
5. **Continuous approximation** - Uses discrete steps

## Conclusion

This simulator helps you:
- ✅ Avoid unprofitable strategies
- ✅ Identify optimal parameter ranges
- ✅ Understand key risk factors
- ✅ Compare different market conditions
- ✅ Make data-driven decisions

**Remember:** This is a MODEL, not a guarantee. Real-world results will vary based on actual market conditions, user behavior, and events not captured in the simulation.

---

**Need help?** Open an issue: https://github.com/Figu3/eulerswap-simulator/issues
