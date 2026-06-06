"""Robustness for the energy-spreads stat-arb: block-bootstrap of the Sharpe and
transaction-cost sensitivity (the spread legs turn over, so costs matter here)."""
import numpy as np
import pandas as pd

from .strategy import build_book
from .metrics import performance, vol_target

TD = 252


def block_bootstrap(ret: pd.Series, n=2000, block=21, seed=0):
    r = vol_target(ret).dropna().values
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(len(r) / block))
    sh, dd = np.empty(n), np.empty(n)
    for i in range(n):
        starts = rng.integers(0, len(r) - block, nb)
        samp = np.concatenate([r[s:s + block] for s in starts])[:len(r)]
        sh[i] = samp.mean() / samp.std() * np.sqrt(TD)
        eq = np.cumprod(1 + samp); dd[i] = (eq / np.maximum.accumulate(eq) - 1).min()
    return sh, dd


def cost_sensitivity(prices: pd.DataFrame, mults=(0.0, 1.0, 2.0, 4.0), base_cost=0.02) -> pd.DataFrame:
    """Rebuild the book at increasing transaction-cost levels (x base cost in
    vol-normalized units; base 0.02 ~ a realistic spread-leg cost)."""
    rows = {}
    for m in mults:
        res = build_book(prices, cost=base_cost * m)
        st = performance(vol_target(res["book"]))
        label = "no cost" if m == 0 else f"{m:g}x base"
        rows[label] = {"Sharpe": st["sharpe"], "CAGR": st["cagr"], "MaxDD": st["max_dd"]}
    return pd.DataFrame(rows).T
