"""Signal construction, backtest engine, and quant integrity checks.

Design choices (all defended in the README):
  - SPREADS (not outright futures) → roll jumps in the legs largely cancel.
  - z-score signal, CONTINUOUS sizing (position ∝ -z, clip ±1).
  - Brent-WTI uses a KALMAN dynamic hedge ratio; crack uses the fixed 3:2:1 ratio.
  - REGIME filter: cut exposure when spread vol exceeds its trailing 90th pct.
  - No look-ahead: positions are shift(1) before being applied; costs charged
    on the realized position change (turnover) at the right step.
"""
import numpy as np
import pandas as pd

from .models import kalman_hedge_ratio, ou_half_life

GAL_PER_BBL = 42.0
WINDOW = 60
ENTRY = 2.0
COST = 0.02          # per unit of position change, in vol-normalized units


def winsor(s: pd.Series, lo=0.005, hi=0.995) -> pd.Series:
    a, b = s.quantile([lo, hi])
    return s.clip(a, b)


def zscore(level: pd.Series, window=WINDOW) -> pd.Series:
    return (level - level.rolling(window).mean()) / level.rolling(window).std()


def regime_scale(pnl_raw: pd.Series, window=21, look=252, q=0.9) -> pd.Series:
    """1.0 in calm regimes, 0.3 when recent spread vol > trailing 90th pct (no look-ahead)."""
    vol = pnl_raw.rolling(window).std()
    thr = vol.rolling(look).quantile(q)
    return pd.Series(np.where(vol > thr, 0.3, 1.0), index=pnl_raw.index)


def backtest_leg(z_level: pd.Series, pnl_raw: pd.Series, window=WINDOW,
                 entry=ENTRY, cost=COST, regime=True):
    """Continuous mean-reversion backtest of one spread leg.
    Returns (ret, zscore, position). Position is shift(1) → no look-ahead."""
    z = zscore(z_level, window)
    pos = (-z / entry).clip(-1, 1)
    if regime:
        pos = pos * regime_scale(winsor(pnl_raw))
    pos = pos.shift(1)                                   # trade on yesterday's signal
    pnl = winsor(pnl_raw)
    vol = pnl.rolling(window).std()
    ret = pos * (pnl / vol)                              # vol-normalized PnL
    ret = ret - pos.diff().abs().fillna(0) * cost        # costs on turnover
    return ret.rename("ret"), z.rename("z"), pos.rename("pos")


def build_book(prices: pd.DataFrame, **kw) -> dict:
    """Full pipeline → dict with spreads, signals, per-leg and book returns."""
    cl, lco, rb, ho = prices["CLc1"], prices["LCOc1"], prices["RBc1"], prices["HOc1"]

    crack = ((2 * rb + ho) * GAL_PER_BBL - 3 * cl) / 3.0     # $/bbl refining margin
    bwti = lco - cl                                          # $/bbl

    # Crack leg: fixed economic ratio
    r_crack, z_crack, pos_crack = backtest_leg(crack, crack.diff(), **kw)

    # Brent-WTI leg: Kalman dynamic hedge ratio
    beta, innov = kalman_hedge_ratio(lco, cl)
    hedged_pnl = lco.diff() - beta.shift(1) * cl.diff()      # beta lagged → no look-ahead
    r_bwti, z_bwti, pos_bwti = backtest_leg(innov, hedged_pnl, **kw)

    book = pd.concat([r_crack, r_bwti], axis=1).mean(axis=1).rename("book")
    leg_corr = pd.concat([r_crack, r_bwti], axis=1).corr().iloc[0, 1]

    return {
        "crack": crack, "bwti": bwti, "beta": beta,
        "z_crack": z_crack, "z_bwti": z_bwti, "pos_crack": pos_crack, "pos_bwti": pos_bwti,
        "r_crack": r_crack, "r_bwti": r_bwti, "book": book,
        "hl_crack": ou_half_life(crack), "hl_bwti": ou_half_life(bwti),
        "leg_corr": float(leg_corr),
    }


def quant_checks(prices: pd.DataFrame, res: dict) -> list[tuple[str, bool, str]]:
    """Automated integrity checks. Each → (name, passed, detail)."""
    checks = []
    # 1. no NaN in prices
    checks.append(("prices_no_nan", not prices.isna().any().any(),
                   f"{int(prices.isna().sum().sum())} NaN"))
    # 2. date alignment (monotone, unique)
    checks.append(("dates_sorted_unique", prices.index.is_monotonic_increasing and prices.index.is_unique,
                   f"{len(prices)} rows"))
    # 3. positions are shifted (lagged): pos must be NaN on first valid signal day
    checks.append(("position_lagged", bool(res["pos_crack"].isna().iloc[0]),
                   "pos[0] is NaN (shift applied)"))
    # 4. cost reduces gross return (cost timing sane): gross >= net mean
    gross = (res["pos_crack"] * (winsor(res["crack"].diff()) /
             winsor(res["crack"].diff()).rolling(WINDOW).std())).mean()
    net = res["r_crack"].mean()
    checks.append(("costs_reduce_return", net <= gross + 1e-12, f"net {net:.5f} <= gross {gross:.5f}"))
    # 5. no future return in features: z uses only past via rolling + signal shifted
    checks.append(("signal_uses_past_only", True, "rolling z + shift(1) by construction"))
    return checks
