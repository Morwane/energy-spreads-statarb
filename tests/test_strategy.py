"""Unit tests — run with:  pytest -q

Validate the quant integrity of the backtest: clean data, sane mean-reversion,
look-ahead-free signals, and cost timing.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.data import load_prices
from src.strategy import build_book, quant_checks
from src.models import ou_half_life

DATA = REPO / "data"


@pytest.fixture(scope="module")
def prices():
    return load_prices(DATA)


@pytest.fixture(scope="module")
def res(prices):
    return build_book(prices)


def test_prices_no_nan(prices):
    assert not prices.isna().any().any()
    assert prices.index.is_monotonic_increasing and prices.index.is_unique


def test_half_lives_finite_and_short(res):
    # mean-reversion must be real: finite half-life under ~1 trading year
    assert 0 < res["hl_crack"] < 252
    assert 0 < res["hl_bwti"] < 252


def test_positions_are_lagged(res):
    # shift(1) applied → first position is NaN (no look-ahead)
    assert np.isnan(res["pos_crack"].iloc[0])
    assert np.isnan(res["pos_bwti"].iloc[0])


def test_positions_bounded(res):
    # continuous sizing clipped to ±1 (regime can only shrink it)
    assert res["pos_crack"].abs().max() <= 1.0 + 1e-9
    assert res["pos_bwti"].abs().max() <= 1.0 + 1e-9


def test_legs_weakly_correlated(res):
    # the two legs should diversify, not duplicate each other
    assert abs(res["leg_corr"]) < 0.4


def test_kalman_beta_reasonable(res):
    beta = res["beta"].dropna()
    assert np.isfinite(beta).all()
    assert 0.2 < beta.median() < 1.8       # Brent/WTI hedge ratio ~ order 1


def test_all_quant_checks_pass(prices, res):
    assert all(passed for _, passed, _ in quant_checks(prices, res))


def test_ou_half_life_on_random_walk_is_large():
    # sanity: a pure random walk has no mean-reversion → huge/inf half-life
    import pandas as pd
    rw = pd.Series(np.random.RandomState(0).randn(2000).cumsum())
    assert ou_half_life(rw) > 100 or np.isinf(ou_half_life(rw))
