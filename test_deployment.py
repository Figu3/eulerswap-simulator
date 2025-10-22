#!/usr/bin/env python3
"""
Quick diagnostic to check if deployment will work.
"""

import sys
import subprocess

print("=" * 60)
print("DEPLOYMENT DIAGNOSTICS")
print("=" * 60)

# Check Python version
print(f"\n✓ Python version: {sys.version}")

# Check required modules
required = [
    'streamlit',
    'plotly',
    'pandas',
    'numpy',
    'yaml'
]

print("\n📦 Checking dependencies:")
for module in required:
    try:
        __import__(module)
        print(f"  ✓ {module}")
    except ImportError:
        print(f"  ✗ {module} - MISSING!")

# Check if app.py exists
import os
if os.path.exists('app.py'):
    print("\n✓ app.py found")
else:
    print("\n✗ app.py NOT FOUND")

# Check if sim/ directory exists
if os.path.exists('sim/'):
    print("✓ sim/ directory found")
    if os.path.exists('sim/core.py'):
        print("  ✓ sim/core.py found")
    if os.path.exists('sim/models.py'):
        print("  ✓ sim/models.py found")
else:
    print("✗ sim/ directory NOT FOUND")

# Try importing sim modules
print("\n🔧 Testing imports:")
try:
    from sim.core import SimulationEngine, SimulationParams, PoolState
    print("  ✓ sim.core imports successfully")
except Exception as e:
    print(f"  ✗ sim.core import failed: {e}")

# Test basic simulation
print("\n🧪 Testing simulation engine:")
try:
    from sim.core import SimulationEngine, SimulationParams, PoolState

    params = SimulationParams(
        horizon_days=7,
        steps_per_day=24,
        seed=42,
        amm_type="constant_product",
        fee_bps=7,
        underlying_yield_apr=0.06,
        rehyp_yield_apr=0.12,
        borrow_cost_apr=0.08,
        ops_cost_usd_per_day=150,
        flow_model="deterministic",
        deterministic_schedule_bps=20,
        max_borrow_multiple=0.8,
        peg_deviation_std_bps=5,
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

    print(f"  ✓ Simulation ran successfully!")
    print(f"  ✓ Generated {len(results)} data points")
    print(f"  ✓ Net P&L: ${summary['net_pnl']:,.0f}")

except Exception as e:
    print(f"  ✗ Simulation failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("DEPLOYMENT RECOMMENDATIONS")
print("=" * 60)

print("\n✅ WORKING PLATFORMS:")
print("  1. Streamlit Cloud - https://streamlit.io/cloud (FREE)")
print("  2. Railway - https://railway.app ($5/mo free credit)")
print("  3. Render - https://render.com (FREE tier)")

print("\n❌ NON-WORKING PLATFORMS:")
print("  • Vercel - Does NOT support Python")
print("  • Netlify - Does NOT support Python (static sites only)")
print("  • GitHub Pages - Static sites only")

print("\n📖 Next steps:")
print("  1. Go to https://streamlit.io/cloud")
print("  2. Sign in with GitHub")
print("  3. Click 'New app'")
print("  4. Select 'eulerswap-simulator' repo")
print("  5. Main file: app.py")
print("  6. Advanced: Python version = 3.9+")
print("  7. Advanced: Requirements file = requirements-web.txt")
print("  8. Click 'Deploy'")

print("\n" + "=" * 60)
