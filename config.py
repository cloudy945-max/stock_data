"""
=============================================================================
              A股数据采集系统 - ARM NAS 优化配置
=============================================================================
针对 ARM64/aarch64 架构 NAS 优化：
- 降低并发数减少 CPU 占用
- 增加请求间隔避免过热
- 使用 SQLite 替代 DuckDB（ARM NAS 兼容性更好）
- 单线程操作更稳定

建议硬件配置：
- CPU: 双核 ARM Cortex-A53/A72 及以上
- 内存: 4GB 及以上
- 存储: SSD（推荐）或 HDD（慢速）

部署注意：
- 使用 venv 隔离环境
- cron 定时任务建议在 CPU 空闲时段执行
- 定期清理日志和数据库优化
=============================================================================
"""

import os
from pathlib import Path
from pydantic import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    TUSHARE_TOKEN: str = ""
    AKShare_ENABLED: bool = True
    TUSHARE_ENABLED: bool = True
    
    DATA_DIR: str = str(Path(__file__).parent / "data")
    SQLITE_DB_PATH: str = str(Path(__file__).parent / "data" / "stock_data.db")
    DB_PATH: str = str(Path(__file__).parent / "data" / "stock_data.duckdb")
    
    STOCK_LIST: list = []
    UPDATE_ALL_STOCKS: bool = True
    
    MAX_CONCURRENT: int = 2
    REQUEST_DELAY_MIN: float = 2.5
    REQUEST_DELAY_MAX: float = 6.0
    MAX_RETRIES: int = 5
    
    PYTHONARM_MODE: bool = True
    SQLITE_TIMEOUT: float = 30.0
    
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


DAILY_TABLE_COLUMNS = [
    "ts_code", "trade_date", "open", "high", "low", "close",
    "pre_close", "change", "pct_chg", "volume", "amount",
    "adj_factor", "open_adj", "high_adj", "low_adj", "close_adj"
]


VALUATION_TABLE_COLUMNS = [
    "ts_code", "trade_date", "pe", "pe_ttm", "pb", "ps",
    "ps_ttm", "dv_ratio", "dv_ttm", "total_mv", "circ_mv"
]


FINANCIAL_TABLE_COLUMNS = [
    "ts_code", "ann_date", "f_ann_date", "end_date", "report_type",
    "basic_eps", "diluted_eps", "total_revenue", "operating_revenue",
    "profit_total", "net_profit", "total_assets", "total_liability", "owner_eq"
]


STOCK_BASIC_TABLE_COLUMNS = [
    "ts_code", "symbol", "name", "area", "industry", "list_date", "status"
]


VALUATION_VALIDATION_RULES = {
    "pe": {"min": -100, "max": 1000, "allow_null": True},
    "pe_ttm": {"min": -100, "max": 1000, "allow_null": True},
    "pb": {"min": -10, "max": 100, "allow_null": True},
    "ps": {"min": -50, "max": 500, "allow_null": True},
    "ps_ttm": {"min": -50, "max": 500, "allow_null": True},
    "dv_ratio": {"min": 0, "max": 20, "allow_null": True},
    "dv_ttm": {"min": 0, "max": 20, "allow_null": True},
}
