"""Econometric models: Ornstein-Uhlenbeck half-life + Kalman dynamic hedge ratio."""
import numpy as np
import pandas as pd


def ou_half_life(spread: pd.Series) -> float:
    """Mean-reversion half-life via AR(1): Δsₜ = α + β·sₜ₋₁,  HL = −ln2 / ln(1+β).
    A finite, short half-life is evidence the spread is tradable mean-reverting."""
    s = spread.dropna()
    lag, ds = s.shift(1), s - s.shift(1)
    d = pd.concat([ds.rename("d"), lag.rename("l")], axis=1).dropna()
    A = np.vstack([np.ones(len(d)), d["l"].values]).T
    beta = np.linalg.lstsq(A, d["d"].values, rcond=None)[0][1]
    return float(-np.log(2) / np.log(1 + beta)) if beta < 0 else np.inf


def kalman_hedge_ratio(y: pd.Series, x: pd.Series, delta: float = 1e-4, R: float = 1e-3):
    """Dynamic regression y = α(t) + β(t)·x by Kalman filter (random-walk states).

    Returns (beta_t, innovation_t). The innovation is the one-step prediction
    error computed from the PRIOR state → it is look-ahead-free and is the
    tradable mean-reversion signal.
    """
    n = len(y)
    betas = np.full(n, np.nan)
    innov = np.full(n, np.nan)
    Vw = delta / (1 - delta) * np.eye(2)        # state (process) covariance
    xst = np.zeros(2)                            # [alpha, beta]
    P = np.zeros((2, 2))
    yv, xv = y.values, x.values
    for t in range(n):
        H = np.array([1.0, xv[t]])
        if t > 0:
            P = P + Vw                           # predict
        e = yv[t] - H @ xst                      # innovation (prior state → no look-ahead)
        S = H @ P @ H + R
        K = P @ H / S                            # Kalman gain
        xst = xst + K * e                        # update
        P = P - np.outer(K, H @ P)
        betas[t], innov[t] = xst[1], e
    return pd.Series(betas, index=y.index, name="beta"), pd.Series(innov, index=y.index, name="innov")
