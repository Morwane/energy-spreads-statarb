# Robustness — Energy Spreads Stat-Arb

## Bootstrap confidence (book)

- Sharpe 90% CI **[+0.45, +1.19]**, median +0.83, P(Sharpe>0) = **100%**; max-drawdown 90% CI [-28.1%, -12.1%] (block bootstrap, 2000x, 21-day blocks).

![Bootstrap](docs/assets/robust_bootstrap_sharpe.png)

## Transaction-cost sensitivity

| Cost level | Sharpe | CAGR | Max DD |
|---|--:|--:|--:|
| no cost | +1.03 | +10.4% | -15.5% |
| 1x base | +0.82 | +8.0% | -17.0% |
| 2x base | +0.60 | +5.7% | -20.1% |
| 4x base | +0.17 | +1.2% | -27.7% |

_Base cost ~ a realistic spread-leg charge; the edge survives several times that._

## Two mini case studies

Each leg trades a distinct economic relationship and stands on its own:

| Spread | Economics | Sharpe | OU half-life |
|---|---|--:|--:|
| Crack 3:2:1 (refining margin) | refining margin (crude in, products out) | +0.45 | 61d |
| Brent-WTI (crude basis) | quality/logistics basis between crude benchmarks | +0.78 | 39d |

Leg correlation **+0.07** -> near-independent sources, so the combined book diversifies.

![Case studies](docs/assets/robust_case_studies.png)