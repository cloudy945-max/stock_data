import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TUSHARE_TOKEN: str = ""
    AKShare_ENABLED: bool = True
    TUSHARE_ENABLED: bool = True
    
    DB_PATH: str = str(Path(__file__).parent / "data" / "stock_data.duckdb")
    DATA_DIR: str = str(Path(__file__).parent / "data")
    
    STOCK_LIST: list = []
    UPDATE_ALL_STOCKS: bool = True
    MAX_CONCURRENT: int = 8
    
    REQUEST_DELAY_MIN: float = 1.0
    REQUEST_DELAY_MAX: float = 3.0
    MAX_RETRIES: int = 5
    
    MAIL_ENABLED: bool = False
    PROXY_ENABLED: bool = False
    
    UPDATE_DAILY: bool = True
    UPDATE_VALUATION: bool = True
    UPDATE_FINANCIAL: bool = True
    FINANCIAL_UPDATE_FREQ: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


# ==================== 表结构定义 ====================
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


USER_AGENT_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]
VALUATION_VALIDATION_RULES = {}

# 自动更新财务数据频率（天）
