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