"""Publication-quality figures for the README / tearsheet → docs/assets/*.png."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .metrics import vol_target, performance, subperiod_metrics

plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 130, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 10, "figure.autolayout": True})
BLUE, RED, GREEN, GREY = "#1f5fa8", "#c0392b", "#27ae60", "#7f8c8d"

SUBPERIODS = {"2010-2014": ("2010", "2014"), "2015-2019": ("2015", "2019"),
              "2020-2022": ("2020", "2022"), "2023-2026": ("2023", "2026")}


def _eq(r):
    return (1 + vol_target(r)).cumprod() - 1


def make_all(res: dict, assets: Path):
    assets = Path(assets); assets.mkdir(parents=True, exist_ok=True)
    book, rc, rb = res["book"], res["r_crack"], res["r_bwti"]

    # 1 — equity curve (book + legs, each vol-targeted to 10%)
    fig, ax = plt.subplots(figsize=(10, 4.6))
    for r, nm, c, w in [(book, "Combined book", BLUE, 1.8),
                        (rc, "Crack 3:2:1 leg", GREEN, 1.0), (rb, "Brent-WTI leg", RED, 1.0)]:
        e = _eq(r)
        ax.plot(e.index, e * 100, color=c, lw=w, label=f"{nm}  (Sharpe {performance(vol_target(r))['sharpe']:+.2f})")
    ax.set_title("Energy Spreads Stat-Arb — Cumulative Performance (vol-targeted 10%)", fontweight="bold")
    ax.set_ylabel("cumulative return (%)"); ax.legend(loc="upper left", fontsize=9)
    fig.savefig(assets / "strategy_equity_curve.png"); plt.close(fig)

    # 2 — drawdown
    e = (1 + vol_target(book)).cumprod(); dd = (e / e.cummax() - 1) * 100
    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.fill_between(dd.index, dd, color=RED, alpha=.4)
    ax.set_title("Drawdown Profile — Combined Book", fontweight="bold"); ax.set_ylabel("drawdown (%)")
    fig.savefig(assets / "strategy_drawdown.png"); plt.close(fig)

    # 3 & 4 — z-score + positions
    for z, pos, ttl, fname in [(res["z_crack"], res["pos_crack"], "3:2:1 Crack Spread", "spread_zscore_trades_crack"),
                               (res["z_bwti"], res["pos_bwti"], "Brent-WTI Spread", "spread_zscore_trades_brent_wti")]:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(z.index, z, color=GREY, lw=.7, label="z-score")
        for lv in (2, -2): ax.axhline(lv, color=RED, ls="--", lw=.8)      # entry ±2
        for lv in (.5, -.5): ax.axhline(lv, color=GREEN, ls=":", lw=.8)   # exit ±0.5
        ax2 = ax.twinx(); ax2.fill_between(pos.index, pos, color=BLUE, alpha=.22); ax2.set_ylim(-3, 3)
        ax2.set_ylabel("position (∝ −z)")
        ax.set_title(f"{ttl} — Z-Score Signal with Hysteresis (entry ±2, exit ±0.5)", fontweight="bold")
        ax.set_ylabel("z-score"); ax.legend(loc="upper left", fontsize=8)
        fig.savefig(assets / f"{fname}.png"); plt.close(fig)

    # 5 — rolling correlation between legs
    rcorr = rc.rolling(126).corr(rb)
    fig, ax = plt.subplots(figsize=(10, 3.4))
    ax.plot(rcorr.index, rcorr, color=BLUE, lw=1); ax.axhline(0, color="black", lw=.7)
    ax.axhline(res["leg_corr"], color=RED, ls="--", lw=.8, label=f"full-sample ρ={res['leg_corr']:+.2f}")
    ax.set_title("Rolling 126d Correlation Between Spread Legs (low ρ → diversification)", fontweight="bold")
    ax.set_ylabel("correlation"); ax.legend(fontsize=8)
    fig.savefig(assets / "rolling_correlation_legs.png"); plt.close(fig)

    # 6 — Kalman beta
    beta = res["beta"]
    fig, ax = plt.subplots(figsize=(10, 3.4))
    ax.plot(beta.index, beta, color=BLUE, lw=1); ax.axhline(1.0, color=GREY, ls="--", lw=.8, label="static 1:1")
    ax.set_title("Kalman Dynamic Hedge Ratio  β(t):  Brent = α + β·WTI", fontweight="bold")
    ax.set_ylabel("β"); ax.legend(fontsize=8)
    fig.savefig(assets / "kalman_hedge_ratio.png"); plt.close(fig)

    # 7 — subperiod robustness (book Sharpe)
    sp = subperiod_metrics(vol_target(book), SUBPERIODS)
    fig, ax = plt.subplots(figsize=(8, 3.6))
    colors = [BLUE if v >= 0 else RED for v in sp["sharpe"]]
    ax.bar(sp.index, sp["sharpe"], color=colors, alpha=.85)
    ax.axhline(0, color="black", lw=.7)
    for i, v in enumerate(sp["sharpe"]): ax.text(i, v + (.03 if v >= 0 else -.08), f"{v:+.2f}", ha="center", fontsize=9)
    ax.set_title("Subperiod Robustness — Book Sharpe by Regime Era", fontweight="bold"); ax.set_ylabel("Sharpe")
    fig.savefig(assets / "subperiod_robustness.png"); plt.close(fig)

    # 8 — performance summary table
    rows = {"Crack 3:2:1": performance(vol_target(rc), res["pos_crack"]),
            "Brent-WTI": performance(vol_target(rb), res["pos_bwti"]),
            "Combined book": performance(vol_target(book))}
    keys = [("sharpe", "Sharpe", "{:+.2f}"), ("cagr", "CAGR", "{:.1%}"), ("vol", "Vol", "{:.1%}"),
            ("max_dd", "Max DD", "{:.1%}"), ("calmar", "Calmar", "{:+.2f}"), ("hit", "Hit", "{:.0%}"),
            ("var95", "VaR95", "{:.2%}"), ("es95", "ES95", "{:.2%}"), ("skew", "Skew", "{:+.2f}"),
            ("kurt", "Kurt", "{:+.1f}")]
    table = [[fmt.format(m.get(k, np.nan)) for k, _, fmt in keys] for m in rows.values()]
    fig, ax = plt.subplots(figsize=(11, 2.2)); ax.axis("off")
    t = ax.table(cellText=table, rowLabels=list(rows), colLabels=[lbl for _, lbl, _ in keys],
                 cellLoc="center", loc="center")
    t.auto_set_font_size(False); t.set_fontsize(9.5); t.scale(1, 1.5)
    ax.set_title("Performance Summary (vol-targeted to 10% annual)", fontweight="bold", pad=14)
    fig.savefig(assets / "performance_summary_table.png", bbox_inches="tight"); plt.close(fig)

    return list(SUBPERIODS), rows
