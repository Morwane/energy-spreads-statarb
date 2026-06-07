# Energy Spreads Stat-Arb — Strategy Tearsheet

Period: **2010-01-04 → 2026-06-04** (4132 trading days). All returns vol-targeted to 10% annual.

## Executive summary
A market-neutral relative-value book combining the 3:2:1 crack spread and the Brent-WTI spread. Combined **Sharpe +0.79**, CAGR +7.7%, max drawdown -17.0%, Calmar +0.45. The two legs are weakly correlated (ρ=+0.07) → genuine diversification.

## Data universe
- WTI `CLc1`, Brent `LCOc1` ($/bbl); RBOB `RBc1`, Heating Oil `HOc1` ($/gal). LSEG continuation futures, 2010-2026.

## Spread construction & unit conversion
- **3:2:1 crack** = `[2·RBOB·42 + 1·HeatOil·42 − 3·WTI] / 3` ($/bbl). The ×42 converts $/gal → $/bbl.
- **Brent-WTI** = `LCOc1 − CLc1` ($/bbl).

## Roll methodology
Continuation series are NOT roll-adjusted, but **spreads are roll-robust**: legs roll on similar schedules so roll jumps largely cancel. Residual jumps are winsorized (0.5%/99.5%).

## Mean-reversion (OU half-life)
- Crack: **61 days** | Brent-WTI: **33 days** — finite & short → tradable.

## Signal & hysteresis
Rolling 60d z-score; **continuous** sizing position = clip(−z/2, −1, 1). Brent-WTI uses a **Kalman dynamic hedge ratio**; the regime filter cuts exposure to 30% when spread vol exceeds its trailing 90th percentile.

## Transaction costs
0.02 (vol-normalized units) charged on every unit of position change (turnover).

## Performance
| Strategy | Sharpe | CAGR | Vol | Max DD | Calmar | Hit | VaR95 | ES95 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| Crack 3:2:1 | +0.45 | +4.1% | 10.0% | -21.3% | +0.19 | 50% | 0.90% | 1.51% |
| Brent-WTI | +0.75 | +7.2% | 10.0% | -20.2% | +0.36 | 48% | 0.75% | 1.36% |
| Combined book | +0.79 | +7.7% | 10.0% | -17.0% | +0.45 | 51% | 0.85% | 1.40% |

![Equity](../docs/assets/strategy_equity_curve.png)
![Drawdown](../docs/assets/strategy_drawdown.png)

## Robustness — subperiods
| Period | Sharpe | CAGR | Max DD |
|---|--:|--:|--:|
| 2010-2014 | +0.36 | +3.3% | -17.0% |
| 2015-2019 | +0.87 | +8.8% | -13.4% |
| 2020-2022 | +0.30 | +2.5% | -14.7% |
| 2023-2026 | +1.86 | +17.8% | -8.3% |

![Subperiods](../docs/assets/subperiod_robustness.png)

### Parameter sensitivity
Combined-book Sharpe across (window, entry) grid ranges **0.70 – 0.84** — a stable surface, so the edge is not cherry-picked to one parameter set.

![Sensitivity](../docs/assets/parameter_sensitivity.png)

## Risk controls
- No look-ahead: z uses only past data; positions `shift(1)` before applied to returns.
- Costs charged on realized turnover. Vol-targeting for interpretable risk.
- Automated integrity checks in `src/strategy.py:quant_checks` (run via `run_backtest.py`).

## Limitations
- Vol-normalized PnL scaled to 10% target — not a sized dollar book with real fills.
- Continuation-series & roll approximations; winsorization uses full-sample quantiles (outlier clip only).
- Brent (ICE) / WTI (NYMEX) roll on slightly different schedules → residual noise.
- Research only, not investment advice.

## Next steps
- Cointegration tests (Johansen) for formal pair validation; HMM regime gating; combine with a vol-carry leg into a multi-strategy risk-parity book.