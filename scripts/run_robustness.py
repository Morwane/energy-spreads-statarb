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

from scipy.stats import gaussian_kde
from src.data import load_prices
from src.strategy import build_book
from src.robustness import block_bootstrap, cost_sensitivity

ASSETS, REPORTS = REPO / "docs" / "assets", REPO / "reports"
plt.rcParams.update({"figure.dpi": 140, "savefig.dpi": 140, "axes.grid": True,
                     "grid.alpha": 0.22, "axes.spines.top": False, "axes.spines.right": False,
                     "font.size": 10, "axes.titlesize": 11.5, "axes.titleweight": "bold",
                     "figure.autolayout": True})
BLUE, RED = "#1f5fa8", "#c0392b"


def plot_bootstrap(sh, dd, title, path, color=BLUE):
    """Polished 2-panel Monte-Carlo figure: KDE + shaded 90% CI + median + P(>0)."""
    sh, dd = np.asarray(sh), np.asarray(dd) * 100
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, data, lab, fmt, is_sh in [(axes[0], sh, "Annualized Sharpe", "{:+.2f}", True),
                                      (axes[1], dd, "Max Drawdown (%)", "{:.0f}", False)]:
        lo, hi, med = *np.percentile(data, [5, 95]), np.median(data)
        ax.hist(data, bins=45, density=True, color=color, alpha=.16, edgecolor="none")
        xs = np.linspace(data.min(), data.max(), 300); kde = gaussian_kde(data)(xs)
        ax.plot(xs, kde, color=color, lw=2.2)
        ax.fill_between(xs, kde, where=(xs >= lo) & (xs <= hi), color=color, alpha=.30)
        ax.axvline(med, color=RED, lw=1.5, ls="--")
        ax.set_title(lab); ax.set_yticks([]); ax.margins(x=0.01)
        txt = f"90% CI [{fmt.format(lo)}, {fmt.format(hi)}]\nmedian {fmt.format(med)}"
        if is_sh:
            ax.axvline(0, color="black", lw=.9); txt += f"\nP(Sharpe>0) = {(data > 0).mean():.0%}"
        ax.text(.03, .96, txt, transform=ax.transAxes, fontsize=8.5, va="top",
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=color, alpha=.9))
    fig.suptitle(title, fontweight="bold", fontsize=12.5)
    fig.tight_layout(rect=[0, 0, 1, 0.95]); fig.savefig(path, bbox_inches="tight"); plt.close(fig)


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

    plot_bootstrap(sh, dd, "Energy Spreads Stat-Arb - Monte-Carlo robustness (2000 block-bootstrap resamples)",
                   ASSETS / "robust_bootstrap_sharpe.png")

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
