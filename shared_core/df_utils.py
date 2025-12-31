# shared_core/foundation/df_utils.py
from typing import Iterable
import pandas as pd

def safe_concat(dfs: Iterable[pd.DataFrame]) -> pd.DataFrame:
    """
    Concatenate DataFrames safely; ignores None/empty inputs.
    """
    valid = [df for df in dfs if isinstance(df, pd.DataFrame) and not df.empty]
    if not valid:
        return pd.DataFrame()
    return pd.concat(valid, axis=0)

def ensure_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure DataFrame index is DatetimeIndex (UTC-naive).
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        df.index = pd.to_datetime(df.index)
    return df

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names: lowercase + underscore.
    """
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df

def drop_na_safely(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows that are fully NA only.
    """
    return df.dropna(how="all")
