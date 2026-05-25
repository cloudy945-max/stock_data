"""
SQLite 存储层 - ARM NAS 优化版
使用 SQLAlchemy + SQLite，保持与 DuckDB 版本相同的接口
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict
from threading import Lock
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from config import settings, VALUATION_TABLE_COLUMNS, FINANCIAL_TABLE_COLUMNS, STOCK_BASIC_TABLE_COLUMNS, DAILY_TABLE_COLUMNS


class SQLiteStorage:
    _engine = None
    _lock = Lock()
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.SQLITE_DB_PATH
        self._ensure_dir()
        self._init_engine()
    
    @classmethod
    def _init_engine(cls):
        with cls._lock:
            if cls._engine is None:
                db_url = f"sqlite:///{settings.SQLITE_DB_PATH}"
                cls._engine = create_engine(
                    db_url,
                    poolclass=QueuePool,
                    pool_size=2,
                    max_overflow=2,
                    pool_timeout=30,
                    pool_pre_ping=True,
                    connect_args={
                        "timeout": getattr(settings, 'SQLITE_TIMEOUT', 30.0),
                        "check_same_thread": False
                    }
                )
    
    def _get_session(self) -> Session:
        if SQLiteStorage._engine is None:
            self._init_engine()
        SessionLocal = sessionmaker(bind=SQLiteStorage._engine)
        return SessionLocal()
    
    def _ensure_dir(self):
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def init_tables(self):
        session = self._get_session()
        try:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS daily (
                    ts_code TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    pre_close REAL,
                    change REAL,
                    pct_chg REAL,
                    volume INTEGER,
                    amount INTEGER,
                    adj_factor REAL,
                    open_adj REAL,
                    high_adj REAL,
                    low_adj REAL,
                    close_adj REAL,
                    PRIMARY KEY (ts_code, trade_date)
                )
            """))
            
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS valuation (
                    ts_code TEXT NOT NULL,
                    trade_date TEXT NOT NULL,
                    pe REAL,
                    pe_ttm REAL,
                    pb REAL,
                    ps REAL,
                    ps_ttm REAL,
                    dv_ratio REAL,
                    dv_ttm REAL,
                    total_mv INTEGER,
                    circ_mv INTEGER,
                    PRIMARY KEY (ts_code, trade_date)
                )
            """))
            
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS financial (
                    ts_code TEXT NOT NULL,
                    ann_date TEXT,
                    f_ann_date TEXT,
                    end_date TEXT NOT NULL,
                    report_type INTEGER,
                    basic_eps REAL,
                    diluted_eps REAL,
                    total_revenue INTEGER,
                    operating_revenue INTEGER,
                    profit_total INTEGER,
                    net_profit INTEGER,
                    total_assets INTEGER,
                    total_liability INTEGER,
                    owner_eq INTEGER,
                    PRIMARY KEY (ts_code, end_date, report_type)
                )
            """))
            
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS stock_basic (
                    ts_code TEXT PRIMARY KEY,
                    symbol TEXT,
                    name TEXT,
                    area TEXT,
                    industry TEXT,
                    list_date TEXT,
                    status TEXT
                )
            """))
            
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_daily_trade ON daily(trade_date)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_valuation_trade ON valuation(trade_date)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_financial_end ON financial(end_date)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_stock_status ON stock_basic(status)"))
            
            session.commit()
        finally:
            session.close()
    
    def get_latest_date(self, table_name: str, ts_code: str) -> Optional[str]:
        session = self._get_session()
        try:
            query = text(f"SELECT MAX(trade_date) FROM {table_name} WHERE ts_code = :ts_code")
            result = session.execute(query, {"ts_code": ts_code}).fetchone()
            return result[0] if result and result[0] else None
        finally:
            session.close()
    
    def get_latest_financial_date(self, ts_code: str) -> Optional[str]:
        session = self._get_session()
        try:
            query = text("SELECT MAX(end_date) FROM financial WHERE ts_code = :ts_code")
            result = session.execute(query, {"ts_code": ts_code}).fetchone()
            return result[0] if result and result[0] else None
        finally:
            session.close()
    
    def insert_or_update(self, table_name: str, df: pd.DataFrame):
        if df.empty:
            return 0
        
        df = df.copy().where(pd.notnull(df), None)
        
        session = self._get_session()
        try:
            columns = df.columns.tolist()
            
            if table_name == "daily":
                placeholders = ", ".join([f":{col}" for col in columns])
                insert_sql = text(f"""
                    INSERT OR REPLACE INTO {table_name} ({", ".join(columns)})
                    VALUES ({placeholders})
                """)
            elif table_name == "valuation":
                placeholders = ", ".join([f":{col}" for col in columns])
                insert_sql = text(f"""
                    INSERT OR REPLACE INTO {table_name} ({", ".join(columns)})
                    VALUES ({placeholders})
                """)
            else:
                raise ValueError(f"Unsupported table for insert_or_update: {table_name}")
            
            records = df.to_dict(orient='records')
            session.execute(insert_sql, records)
            session.commit()
            
            return len(df)
        finally:
            session.close()
    
    def insert_or_update_financial(self, df: pd.DataFrame):
        if df.empty:
            return 0
        
        df = df.copy().where(pd.notnull(df), None)
        
        session = self._get_session()
        try:
            columns = df.columns.tolist()
            placeholders = ", ".join([f":{col}" for col in columns])
            insert_sql = text(f"""
                INSERT OR REPLACE INTO financial ({", ".join(columns)})
                VALUES ({placeholders})
            """)
            
            records = df.to_dict(orient='records')
            session.execute(insert_sql, records)
            session.commit()
            
            return len(df)
        finally:
            session.close()
    
    def insert_stock_basic(self, df: pd.DataFrame):
        if df.empty:
            return 0
        
        df = df.copy().where(pd.notnull(df), None)
        
        session = self._get_session()
        try:
            columns = df.columns.tolist()
            placeholders = ", ".join([f":{col}" for col in columns])
            insert_sql = text(f"""
                INSERT OR REPLACE INTO stock_basic ({", ".join(columns)})
                VALUES ({placeholders})
            """)
            
            records = df.to_dict(orient='records')
            session.execute(insert_sql, records)
            session.commit()
            
            return len(df)
        finally:
            session.close()
    
    def get_stock_list(self) -> List[str]:
        session = self._get_session()
        try:
            query = text("SELECT ts_code FROM stock_basic WHERE status = 'L'")
            result = session.execute(query).fetchall()
            return [row[0] for row in result]
        finally:
            session.close()
    
    def get_table_row_count(self, table_name: str) -> int:
        session = self._get_session()
        try:
            query = text(f"SELECT COUNT(*) FROM {table_name}")
            result = session.execute(query).fetchone()
            return result[0] if result else 0
        finally:
            session.close()
    
    def get_distinct_dates(self, table_name: str) -> List[str]:
        session = self._get_session()
        try:
            query = text(f"SELECT DISTINCT trade_date FROM {table_name} ORDER BY trade_date")
            result = session.execute(query).fetchall()
            return [str(row[0]) for row in result]
        finally:
            session.close()
    
    def query(self, sql: str, params: Optional[Dict] = None) -> pd.DataFrame:
        session = self._get_session()
        try:
            params = params or {}
            result = session.execute(text(sql), params)
            columns = result.keys()
            data = result.fetchall()
            return pd.DataFrame(data, columns=columns)
        finally:
            session.close()
    
    def vacuum(self):
        session = self._get_session()
        try:
            session.execute(text("VACUUM"))
            session.commit()
        finally:
            session.close()
    
    def analyze(self):
        session = self._get_session()
        try:
            session.execute(text("ANALYZE"))
            session.commit()
        finally:
            session.close()
    
    def close(self):
        if SQLiteStorage._engine:
            SQLiteStorage._engine.dispose()
            SQLiteStorage._engine = None


DuckDBStorage = SQLiteStorage
