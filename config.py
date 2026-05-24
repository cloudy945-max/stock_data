import os
from pathlib import Path
from pydantic import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    TUSHARE_TOKEN: str = ""
    AKShare_ENABLED: bool = True
    TUSHARE_ENABLED: bool = True
    
    DB_PATH: str = str(Path(__file__).parent / "data" / "stock_data.duckdb")
    DATA_DIR: str = str(Path(__file__).parent / "data")
    
    STOCK_LIST: list = []
    UPDATE_ALL_STOCKS: bool = True
    MAX_CONCURRENT: int = 4
    
    REQUEST_DELAY_MIN: float = 1.5
    REQUEST_DELAY_MAX: float = 4.0
    MAX_RETRIES: int = 5
    
    FINANCIAL_UPDATE_FREQ: Literal["daily", "weekly", "monthly"] = "weekly"
    FINANCIAL_WEEKLY_DAY: int = 5
    
    MAIL_ENABLED: bool = False
    MAIL_SMTP_SERVER: str = "smtp.qq.com"
    MAIL_SMTP_PORT: int = 465
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_RECEIVERS: list = []
    
    PROXY_ENABLED: bool = False
    PROXY_URL: str = ""
    
    UPDATE_DAILY: bool = True
    UPDATE_VALUATION: bool = True
    UPDATE_FINANCIAL: bool = True
    
    CONNECTION_POOL_SIZE: int = 8
    
    class Config:
        env_file = ".env"


settings = Settings()


USER_AGENT_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


DAILY_TABLE_SCHEMA = {
    "ts_code": "VARCHAR",
    "trade_date": "DATE",
    "open": "DOUBLE",
    "high": "DOUBLE",
    "low": "DOUBLE",
    "close": "DOUBLE",
    "pre_close": "DOUBLE",
    "change": "DOUBLE",
    "pct_chg": "DOUBLE",
    "volume": "BIGINT",
    "amount": "BIGINT",
    "adj_factor": "DOUBLE",
    "open_adj": "DOUBLE",
    "high_adj": "DOUBLE",
    "low_adj": "DOUBLE",
    "close_adj": "DOUBLE",
}


VALUATION_TABLE_SCHEMA = {
    "ts_code": "VARCHAR",
    "trade_date": "DATE",
    "pe": "DOUBLE",
    "pe_ttm": "DOUBLE",
    "pb": "DOUBLE",
    "ps": "DOUBLE",
    "ps_ttm": "DOUBLE",
    "dv_ratio": "DOUBLE",
    "dv_ttm": "DOUBLE",
    "total_mv": "BIGINT",
    "circ_mv": "BIGINT",
}


FINANCIAL_TABLE_SCHEMA = {
    "ts_code": "VARCHAR",
    "ann_date": "DATE",
    "f_ann_date": "DATE",
    "end_date": "DATE",
    "report_type": "INT",
    "basic_eps": "DOUBLE",
    "diluted_eps": "DOUBLE",
    "total_revenue": "BIGINT",
    "operating_revenue": "BIGINT",
    "profit_total": "BIGINT",
    "net_profit": "BIGINT",
    "total_assets": "BIGINT",
    "total_liability": "BIGINT",
    "owner_eq": "BIGINT",
}


STOCK_BASIC_TABLE_SCHEMA = {
    "ts_code": "VARCHAR",
    "symbol": "VARCHAR",
    "name": "VARCHAR",
    "area": "VARCHAR",
    "industry": "VARCHAR",
    "list_date": "DATE",
    "status": "VARCHAR",
}


VALUATION_VALIDATION_RULES = {
    "pe": {"min": -100, "max": 1000, "allow_null": True},
    "pe_ttm": {"min": -100, "max": 1000, "allow_null": True},
    "pb": {"min": -10, "max": 100, "allow_null": True},
    "ps": {"min": -50, "max": 500, "allow_null": True},
    "ps_ttm": {"min": -50, "max": 500, "allow_null": True},
    "dv_ratio": {"min": 0, "max": 20, "allow_null": True},
    "dv_ttm": {"min": 0, "max": 20, "allow_null": True},
}
