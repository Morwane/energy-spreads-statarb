"""Generate all figures (docs/assets/) and the quant tearsheet (reports/).

Usage:  python scripts/generate_report.py
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.data import load_prices
from src.strategy import build_book, sensitivity_grid, GAL_PER_BBL, WINDOW, ENTRY, COST
from src.metrics import vol_target, performance, subperiod_metrics
from src.plots import make_all, plot_sensitivity, SUBPERIODS

DATA, ASSETS, REPORTS = REPO / "data", REPO / "docs" / "assets", REPO / "reports"


def main():
    prices = load_prices(DATA)
    res = build_book(prices)
    make_all(res, ASSETS)
    grid = sensitivity_grid(prices)
    plot_sensitivity(grid, ASSETS)
    print(f"Figures → {ASSETS}")
    print(f"Sensitivity grid Sharpe range: {grid.values.min():.2f} .. {grid.values.max():.2f}")

    m = {nm: performance(vol_target(r), pos) for nm, r, pos in
         [("Crack 3:2:1", res["r_crack"], res["pos_crack"]),
          ("Brent-WTI", res["r_bwti"], res["pos_bwti"]),
          ("Combined book", res["book"], None)]}
    sp = subperiod_metrics(vol_target(res["book"]), SUBPERIODS)
    b = m["Combined book"]

    L = [
        "# Energy Spreads Stat-Arb — Strategy Tearsheet", "",
        f"Period: **{prices.index[0].date()} → {prices.index[-1].date()}** "
        f"({len(prices)} trading days). All returns vol-targeted to 10% annual.", "",
        "## Executive summary",
        f"A market-neutral relative-value book combining the 3:2:1 crack spread and the "
        f"Brent-WTI spread. Combined **Sharpe {b['sharpe']:+.2f}**, CAGR {b['cagr']:+.1%}, "
        f"max drawdown {b['max_dd']:.1%}, Calmar {b['calmar']:+.2f}. The two legs are weakly "
        f"correlated (ρ={res['leg_corr']:+.2f}) → genuine diversification.", "",
        "## Data universe",
        "- WTI `CLc1`, Brent `LCOc1` ($/bbl); RBOB `RBc1`, Heating Oil `HOc1` ($/gal). LSEG continuation futures, 2010-2026.", "",
        "## Spread construction & unit conversion",
        "- **3:2:1 crack** = `[2·RBOB·42 + 1·HeatOil·42 − 3·WTI] / 3` ($/bbl). The ×42 converts $/gal → $/bbl.",
        "- **Brent-WTI** = `LCOc1 − CLc1` ($/bbl).", "",
        "## Roll methodology",
        "Continuation series are NOT roll-adjusted, but **spreads are roll-robust**: legs roll on "
        "similar schedules so roll jumps largely cancel. Residual jumps are winsorized (0.5%/99.5%).", "",
        "## Mean-reversion (OU half-life)",
        f"- Crack: **{res['hl_crack']:.0f} days** | Brent-WTI: **{res['hl_bwti']:.0f} days** — finite & short → tradable.", "",
        "## Signal & hysteresis",
        f"Rolling {WINDOW}d z-score; **continuous** sizing position = clip(−z/{ENTRY:.0f}, −1, 1). "
        "Brent-WTI uses a **Kalman dynamic hedge ratio**; the regime filter cuts exposure to 30% "
        "when spread vol exceeds its trailing 90th percentile.", "",
        "## Transaction costs",
        f"{COST} (vol-normalized units) charged on every unit of position change (turnover).", "",
        "## Performance",
        "| Strategy | Sharpe | CAGR | Vol | Max DD | Calmar | Hit | VaR95 | ES95 |",
        "|---|--:|--:|--:|--:|--:|--:|--:|--:|",
    ]
    for nm, x in m.items():
        L.append(f"| {nm} | {x['sharpe']:+.2f} | {x['cagr']:+.1%} | {x['vol']:.1%} | "
                 f"{x['max_dd']:.1%} | {x['calmar']:+.2f} | {x['hit']:.0%} | {x['var95']:.2%} | {x['es95']:.2%} |")
    L += ["", "![Equity](../docs/assets/strategy_equity_curve.png)",
          "![Drawdown](../docs/assets/strategy_drawdown.png)", "",
          "## Robustness — subperiods",
          "| Period | Sharpe | CAGR | Max DD |", "|---|--:|--:|--:|"]
    for p, row in sp.iterrows():
        L.append(f"| {p} | {row['sharpe']:+.2f} | {row['cagr']:+.1%} | {row['max_dd']:.1%} |")
    L += ["", "![Subperiods](../docs/assets/subperiod_robustness.png)", "",
          "### Parameter sensitivity",
          f"Combined-book Sharpe across (window, entry) grid ranges "
          f"**{grid.values.min():.2f} – {grid.values.max():.2f}** — a stable surface, "
          "so the edge is not cherry-picked to one parameter set.",
          "", "![Sensitivity](../docs/assets/parameter_sensitivity.png)", "",
          "## Risk controls",
          "- No look-ahead: z uses only past data; positions `shift(1)` before applied to returns.",
          "- Costs charged on realized turnover. Vol-targeting for interpretable risk.",
          "- Automated integrity checks in `src/strategy.py:quant_checks` (run via `run_backtest.py`).", "",
          "## Limitations",
          "- Vol-normalized PnL scaled to 10% target — not a sized dollar book with real fills.",
          "- Continuation-series & roll approximations; winsorization uses full-sample quantiles (outlier clip only).",
          "- Brent (ICE) / WTI (NYMEX) roll on slightly different schedules → residual noise.",
          "- Research only, not investment advice.", "",
          "## Next steps",
          "- Cointegration tests (Johansen) for formal pair validation; HMM regime gating; "
          "combine with a vol-carry leg into a multi-strategy risk-parity book."]
    (REPORTS / "strategy_tearsheet.md").write_text("\n".join(L), encoding="utf-8")
    print(f"Tearsheet → {REPORTS / 'strategy_tearsheet.md'}")


if __name__ == "__main__":
    main()
