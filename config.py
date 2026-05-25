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
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TUSHARE_TOKEN: str = ""
    AKShare_ENABLED: bool = True
    TUSHARE_ENABLED: bool = True
    
    DATA_DIR: str = str(Path(__file__).parent / "data")
    SQLITE_DB_PATH: str = str(Path(__file__).parent / "data" / "stock_data.db")
    DB_PATH: str = str(Path(__file__).parent / "data" / "stock_data.duckdb")
    
    STOCK_LIST: list = []
    UPDATE_ALL_STOCKS: bool = True
<<<<<<< HEAD
    
    MAX_CONCURRENT: int = 2
    REQUEST_DELAY_MIN: float = 2.5
    REQUEST_DELAY_MAX: float = 6.0
    MAX_RETRIES: int = 5
    
    PYTHONARM_MODE: bool = True
    SQLITE_TIMEOUT: float = 30.0
    
    FINANCIAL_UPDATE_FREQ: Literal["daily", "weekly", "monthly"] = "weekly"
    FINANCIAL_WEEKLY_DAY: int = 5
    
=======
    MAX_CONCURRENT: int = 8
    
    REQUEST_DELAY_MIN: float = 1.0
    REQUEST_DELAY_MAX: float = 3.0
    MAX_RETRIES: int = 5
    
>>>>>>> fd87bc8 (修复项目bug：数据库连接、定时任务、配置、日志)
    MAIL_ENABLED: bool = False
    PROXY_ENABLED: bool = False
    
    UPDATE_DAILY: bool = True
    UPDATE_VALUATION: bool = True
    UPDATE_FINANCIAL: bool = True
<<<<<<< HEAD
    
=======
    FINANCIAL_UPDATE_FREQ: int = 30

>>>>>>> fd87bc8 (修复项目bug：数据库连接、定时任务、配置、日志)
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


<<<<<<< HEAD
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
=======
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
>>>>>>> fd87bc8 (修复项目bug：数据库连接、定时任务、配置、日志)


USER_AGENT_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]
VALUATION_VALIDATION_RULES = {}

# 自动更新财务数据频率（天）
