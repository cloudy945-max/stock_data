import pandas as pd
import numpy as np
from typing import Optional


def normalize_ts_code(ts_code: str) -> str:
    ts_code = str(ts_code).strip().upper()
    
    if ts_code.endswith(".SH") or ts_code.endswith(".SZ"):
        return ts_code
    
    if len(ts_code) == 6:
        if ts_code.startswith(("6", "9")):
            return f"{ts_code}.SH"
        elif ts_code.startswith(("0", "2", "3")):
            return f"{ts_code}.SZ"
    
    return ts_code


def normalize_date(date_str: str) -> str:
    if pd.isna(date_str):
        return None
    
    date_str = str(date_str).strip()
    
    if len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    
    try:
        dt = pd.to_datetime(date_str)
        return dt.strftime("%Y-%m-%d")
    except:
        return None


def normalize_trade_date(df: pd.DataFrame, date_col: str = "trade_date") -> pd.DataFrame:
    if date_col not in df.columns:
        return df
    
    df = df.copy()
    df[date_col] = df[date_col].apply(normalize_date)
    df = df.dropna(subset=[date_col])
    
    return df


def standardize_daily_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    required_cols = ["ts_code", "trade_date", "open", "high", "low", "close", "volume", "amount"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = np.nan
    
    df["ts_code"] = df["ts_code"].apply(normalize_ts_code)
    df = normalize_trade_date(df)
    
    numeric_cols = ["open", "high", "low", "close", "pre_close", "change", "pct_chg", "volume", "amount", "adj_factor"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    if "adj_factor" in df.columns:
        df["adj_factor"] = df["adj_factor"].fillna(1.0)
        for price_col in ["open", "high", "low", "close"]:
            if price_col in df.columns:
                df[f"{price_col}_adj"] = df[price_col] * df["adj_factor"]
    
    df = df.drop_duplicates(subset=["ts_code", "trade_date"])
    df = df.sort_values(by=["ts_code", "trade_date"])
    
    return df


def standardize_valuation_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    required_cols = ["ts_code", "trade_date", "pe", "pb", "ps", "dv_ratio", "total_mv", "circ_mv"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = np.nan
    
    df["ts_code"] = df["ts_code"].apply(normalize_ts_code)
    df = normalize_trade_date(df)
    
    numeric_cols = ["pe", "pe_ttm", "pb", "ps", "ps_ttm", "dv_ratio", "dv_ttm", "total_mv", "circ_mv"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    df = df.drop_duplicates(subset=["ts_code", "trade_date"])
    df = df.sort_values(by=["ts_code", "trade_date"])
    
    return df


def standardize_financial_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    df["ts_code"] = df["ts_code"].apply(normalize_ts_code)
    
    date_cols = ["ann_date", "f_ann_date", "end_date"]
    for col in date_cols:
        if col in df.columns:
            df[col] = df[col].apply(normalize_date)
    
    numeric_cols = ["report_type", "basic_eps", "diluted_eps", "total_revenue", 
                   "operating_revenue", "profit_total", "net_profit", 
                   "total_assets", "total_liability", "owner_eq"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    df = df.drop_duplicates(subset=["ts_code", "end_date", "report_type"])
    df = df.sort_values(by=["ts_code", "end_date"])
    
    return df


def filter_trading_days(df: pd.DataFrame, trade_date_col: str = "trade_date") -> pd.DataFrame:
    df = df.copy()
    df[trade_date_col] = pd.to_datetime(df[trade_date_col])
    df = df[df[trade_date_col].dt.weekday < 5]
    df[trade_date_col] = df[trade_date_col].dt.strftime("%Y-%m-%d")
    return df


def remove_outliers(df: pd.DataFrame, columns: list, z_threshold: float = 3.0) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col in df.columns:
            z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
            df = df[z_scores < z_threshold]
    return df
