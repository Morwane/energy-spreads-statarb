# Robustness — Energy Spreads Stat-Arb

## Bootstrap confidence (book)

- Sharpe 90% CI **[+0.43, +1.17]**, median +0.80, P(Sharpe>0) = **100%**; max-drawdown 90% CI [-28.8%, -12.2%] (block bootstrap, 2000x, 21-day blocks).

![Bootstrap](docs/assets/robust_bootstrap_sharpe.png)

## Transaction-cost sensitivity

| Cost level | Sharpe | CAGR | Max DD |
|---|--:|--:|--:|
| no cost | +1.01 | +10.1% | -15.4% |
| 1x base | +0.79 | +7.7% | -17.0% |
| 2x base | +0.58 | +5.4% | -20.2% |
| 4x base | +0.15 | +1.0% | -27.8% |

_Base cost ~ a realistic spread-leg charge; the edge survives several times that._

## Two mini case studies

Each leg trades a distinct economic relationship and stands on its own:

| Spread | Economics | Sharpe | OU half-life |
|---|---|--:|--:|
| Crack 3:2:1 (refining margin) | refining margin (crude in, products out) | +0.45 | 61d |
| Brent-WTI (crude basis) | quality/logistics basis between crude benchmarks | +0.75 | 33d |

Leg correlation **+0.07** -> near-independent sources, so the combined book diversifies.

![Case studies](docs/assets/robust_case_studies.png)