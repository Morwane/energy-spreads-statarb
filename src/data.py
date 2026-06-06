"""Data loading for the energy-spreads stat-arb engine.

Continuation futures (LSEG): CLc1 (WTI), LCOc1 (Brent), RBc1 (RBOB gasoline),
HOc1 (heating oil / ULSD). WTI/Brent in $/bbl, RBOB/HO in $/gallon.
"""
from pathlib import Path
import pandas as pd

RICS = ["CLc1", "LCOc1", "RBc1", "HOc1"]


def load_prices(data_dir: Path) -> pd.DataFrame:
    """Load the four futures into one aligned, NaN-free price frame."""
    raw = Path(data_dir) / "raw_prices"
    cols = {}
    for ric in RICS:
        s = pd.read_csv(raw / f"{ric}.csv", parse_dates=["Date"], index_col="Date").iloc[:, 0]
        cols[ric] = s.astype(float).sort_index()
    df = pd.concat(cols, axis=1).dropna()
    df.index.name = "Date"
    return df


def fetch_from_lseg(data_dir: Path, start="2010-01-01", end="2026-06-05") -> None:
    """Refresh the CSVs from LSEG (requires an active Workspace session)."""
    import lseg.data as ld
    raw = Path(data_dir) / "raw_prices"; raw.mkdir(parents=True, exist_ok=True)
    ld.open_session()
    try:
        for ric in RICS:
            df = ld.get_history(universe=ric, fields=["TRDPRC_1"], interval="daily",
                                start=start, end=end)
            s = df.iloc[:, 0].dropna(); s.index = pd.to_datetime(s.index)
            s.sort_index().to_csv(raw / f"{ric}.csv", header=["TRDPRC_1"], index_label="Date")
            print(f"  saved {ric}: {len(s)} obs")
    finally:
        ld.close_session()
