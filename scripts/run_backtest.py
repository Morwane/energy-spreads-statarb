"""Run the energy-spreads stat-arb backtest: print metrics, run integrity checks, save results.

Usage:  python scripts/run_backtest.py
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import pandas as pd
from src.data import load_prices
from src.strategy import build_book, quant_checks
from src.metrics import vol_target, performance

DATA = REPO / "data"


def main():
    prices = load_prices(DATA)
    res = build_book(prices)

    print("=" * 74)
    print("ENERGY SPREADS STAT-ARB — backtest")
    print(f"Period: {prices.index[0].date()} → {prices.index[-1].date()}  ({len(prices)} days)")
    print(f"OU half-life: crack {res['hl_crack']:.0f}d | Brent-WTI {res['hl_bwti']:.0f}d "
          f"| leg correlation {res['leg_corr']:+.2f}")
    print("-" * 74)
    print(f"{'Strategy':16} | Sharpe | CAGR  | Vol   | MaxDD  | Calmar | Hit")
    for nm, r, pos in [("Crack 3:2:1", res["r_crack"], res["pos_crack"]),
                       ("Brent-WTI", res["r_bwti"], res["pos_bwti"]),
                       ("Combined book", res["book"], None)]:
        m = performance(vol_target(r), pos)
        print(f"{nm:16} | {m['sharpe']:+.2f}  | {m['cagr']:+.1%} | {m['vol']:.1%} | "
              f"{m['max_dd']:.1%} | {m['calmar']:+.2f}  | {m['hit']:.0%}")

    print("-" * 74)
    print("Quant integrity checks:")
    ok_all = True
    for name, passed, detail in quant_checks(prices, res):
        ok_all &= passed
        print(f"  [{'PASS' if passed else 'FAIL'}] {name:24} — {detail}")
    print("=" * 74)
    print("ALL CHECKS PASSED" if ok_all else "SOME CHECKS FAILED")

    out = pd.DataFrame({"crack": res["crack"], "bwti": res["bwti"], "beta": res["beta"],
                        "r_crack": res["r_crack"], "r_bwti": res["r_bwti"],
                        "book": res["book"], "book_vt10": vol_target(res["book"])})
    out.to_csv(DATA / "results.csv")
    print(f"Saved: {DATA / 'results.csv'}")


if __name__ == "__main__":
    main()
