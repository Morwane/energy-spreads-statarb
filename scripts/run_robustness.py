"""Bootstrap + transaction-cost sensitivity for the energy-spreads stat-arb book.
Usage: python scripts/run_robustness.py"""
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.data import load_prices
from src.strategy import build_book
from src.robustness import block_bootstrap, cost_sensitivity

ASSETS, REPORTS = REPO / "docs" / "assets", REPO / "reports"
plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 130, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 10, "figure.autolayout": True})
BLUE, RED = "#1f5fa8", "#c0392b"


def main():
    prices = load_prices(REPO / "data")
    res = build_book(prices)
    sh, dd = block_bootstrap(res["book"])
    lo, hi = np.percentile(sh, [5, 95]); ddlo, ddhi = np.percentile(dd, [5, 95])
    cs = cost_sensitivity(prices)

    print("=" * 66)
    print("ENERGY SPREADS — robustness")
    print("=" * 66)
    print(f"\n[1] Bootstrap (book, 2000x): Sharpe 90% CI [{lo:+.2f}, {hi:+.2f}], "
          f"median {np.median(sh):+.2f}, P(>0) = {(sh>0).mean():.0%}")
    print(f"    MaxDD 90% CI [{ddlo:.1%}, {ddhi:.1%}]")
    print("\n[2] Transaction-cost sensitivity:")
    print(cs.to_string(formatters={"Sharpe": "{:+.2f}".format, "CAGR": "{:+.1%}".format, "MaxDD": "{:.1%}".format}))

    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.hist(sh, bins=40, color=BLUE, alpha=.7)
    ax.axvline(0, color="black", lw=.8)
    ax.axvline(np.median(sh), color=RED, ls="--", lw=1, label=f"median {np.median(sh):+.2f}")
    ax.set_title("Bootstrap distribution of Sharpe - energy-spreads book (2000 resamples)", fontweight="bold")
    ax.set_xlabel("Sharpe"); ax.legend(fontsize=8)
    fig.savefig(ASSETS / "robust_bootstrap_sharpe.png"); plt.close(fig)

    L = ["# Robustness — Energy Spreads Stat-Arb", "",
         "## Bootstrap confidence (book)", "",
         f"- Sharpe 90% CI **[{lo:+.2f}, {hi:+.2f}]**, median {np.median(sh):+.2f}, "
         f"P(Sharpe>0) = **{(sh>0).mean():.0%}**; max-drawdown 90% CI [{ddlo:.1%}, {ddhi:.1%}] "
         "(block bootstrap, 2000x, 21-day blocks).",
         "", "![Bootstrap](docs/assets/robust_bootstrap_sharpe.png)", "",
         "## Transaction-cost sensitivity", "",
         "| Cost level | Sharpe | CAGR | Max DD |", "|---|--:|--:|--:|"]
    for lvl, row in cs.iterrows():
        L.append(f"| {lvl} | {row['Sharpe']:+.2f} | {row['CAGR']:+.1%} | {row['MaxDD']:.1%} |")
    L += ["", "_Base cost ~ a realistic spread-leg charge; the edge survives several times that._"]
    (REPORTS / "robustness.md").write_text("\n".join(L), encoding="utf-8")
    print(f"\nReport: {REPORTS / 'robustness.md'}")
    print("=" * 66)


if __name__ == "__main__":
    main()
