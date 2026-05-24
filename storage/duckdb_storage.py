import os
import duckdb
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from queue import Queue, Empty
from threading import Lock
from contextlib import contextmanager
from config import settings, DAILY_TABLE_SCHEMA, VALUATION_TABLE_SCHEMA, FINANCIAL_TABLE_SCHEMA, STOCK_BASIC_TABLE_SCHEMA


class ConnectionPool:
    def __init__(self, db_path: str, pool_size: int = 8):
        self.db_path = db_path
        self._pool_size = pool_size
        self._pool: Queue = Queue(maxsize=pool_size)
        self._lock = Lock()
        self._init_pool()
    
    def _create_connection(self):
        conn = duckdb.connect(self.db_path, read_only=False)
        conn.execute("PRAGMA threads=1")
        return conn
    
    def _init_pool(self):
        for _ in range(self._pool_size):
            self._pool.put(self._create_connection())
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = self._pool.get(timeout=30)
            yield conn
        finally:
            if conn is not None:
                self._pool.put(conn)
    
    def close_all(self):
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Empty:
                break


class DuckDBStorage:
    _pool: Optional[ConnectionPool] = None
    _pool_lock = Lock()
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DB_PATH
        self._ensure_dir()
        self._init_pool()
        self._local_conn = self._get_connection()
    
    @classmethod
    def _init_pool(cls):
        with cls._pool_lock:
            if cls._pool is None:
                pool_size = getattr(settings, 'CONNECTION_POOL_SIZE', 8)
                cls._pool = ConnectionPool(settings.DB_PATH, pool_size)
    
    def _get_connection(self):
        return self._pool.get_connection()
    
    def _ensure_dir(self):
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_table_if_not_exists(self, table_name: str, schema: Dict[str, str], conn=None):
        columns = ", ".join([f"{col} {dtype}" for col, dtype in schema.items()])
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {columns}
            )
        """
        target_conn = conn or self._local_conn
        target_conn.execute(create_sql)
        target_conn.commit()
    
    def _create_unique_index(self, table_name: str, columns: List[str], conn=None):
        index_name = f"idx_{table_name}_{'_'.join(columns)}"
        columns_str = ", ".join(columns)
        create_index_sql = f"""
            CREATE UNIQUE INDEX IF NOT EXISTS {index_name} 
            ON {table_name} ({columns_str})
        """
        target_conn = conn or self._local_conn
        target_conn.execute(create_index_sql)
        target_conn.commit()
    
    def init_tables(self):
        self._create_table_if_not_exists("daily", DAILY_TABLE_SCHEMA)
        self._create_unique_index("daily", ["ts_code", "trade_date"])
        
        self._create_table_if_not_exists("valuation", VALUATION_TABLE_SCHEMA)
        self._create_unique_index("valuation", ["ts_code", "trade_date"])
        
        self._create_table_if_not_exists("financial", FINANCIAL_TABLE_SCHEMA)
        self._create_unique_index("financial", ["ts_code", "end_date", "report_type"])
        
        self._create_table_if_not_exists("stock_basic", STOCK_BASIC_TABLE_SCHEMA)
        self._create_unique_index("stock_basic", ["ts_code"])
        
        self._local_conn.commit()
    
    def get_latest_date(self, table_name: str, ts_code: str) -> Optional[str]:
        with self._pool.get_connection() as conn:
            query = f"""
                SELECT MAX(trade_date) as latest_date 
                FROM {table_name} 
                WHERE ts_code = ?
            """
            result = conn.execute(query, [ts_code]).fetchone()
            if result and result[0]:
                return str(result[0])
            return None
    
    def get_latest_financial_date(self, ts_code: str) -> Optional[str]:
        with self._pool.get_connection() as conn:
            query = """
                SELECT MAX(end_date) as latest_date 
                FROM financial 
                WHERE ts_code = ?
            """
            result = conn.execute(query, [ts_code]).fetchone()
            if result and result[0]:
                return str(result[0])
            return None
    
    def insert_or_update(self, table_name: str, df: pd.DataFrame):
        if df.empty:
            return 0
        
        df = df.copy()
        df = df.where(pd.notnull(df), None)
        
        with self._pool.get_connection() as conn:
            temp_table = f"temp_{table_name}_{pd.Timestamp.now().strftime('%H%M%S%f')}"
            conn.register(temp_table, df)
            
            schema = self._get_schema(table_name)
            columns = ", ".join(schema.keys())
            
            delete_sql = f"""
                DELETE FROM {table_name} 
                WHERE (ts_code, trade_date) IN (
                    SELECT ts_code, trade_date FROM {temp_table}
                )
            """
            
            insert_sql = f"""
                INSERT INTO {table_name} ({columns})
                SELECT {columns} FROM {temp_table}
            """
            
            try:
                conn.execute(delete_sql)
                conn.execute(insert_sql)
                conn.commit()
                return len(df)
            except Exception as e:
                conn.rollback()
                raise e
    
    def insert_or_update_financial(self, df: pd.DataFrame):
        if df.empty:
            return 0
        
        df = df.copy()
        df = df.where(pd.notnull(df), None)
        
        with self._pool.get_connection() as conn:
            temp_table = f"temp_financial_{pd.Timestamp.now().strftime('%H%M%S%f')}"
            conn.register(temp_table, df)
            
            delete_sql = """
                DELETE FROM financial 
                WHERE (ts_code, end_date, report_type) IN (
                    SELECT ts_code, end_date, report_type FROM temp_financial
                )
            """.replace("temp_financial", temp_table)
            
            insert_sql = f"""
                INSERT INTO financial 
                SELECT * FROM {temp_table}
            """
            
            try:
                conn.execute(delete_sql)
                conn.execute(insert_sql)
                conn.commit()
                return len(df)
            except Exception as e:
                conn.rollback()
                raise e
    
    def insert_stock_basic(self, df: pd.DataFrame):
        if df.empty:
            return 0
        
        df = df.copy()
        df = df.where(pd.notnull(df), None)
        
        with self._pool.get_connection() as conn:
            temp_table = f"temp_stock_basic_{pd.Timestamp.now().strftime('%H%M%S%f')}"
            conn.register(temp_table, df)
            
            delete_sql = f"""
                DELETE FROM stock_basic 
                WHERE ts_code IN (SELECT ts_code FROM {temp_table})
            """
            
            insert_sql = f"""
                INSERT INTO stock_basic 
                SELECT * FROM {temp_table}
            """
            
            try:
                conn.execute(delete_sql)
                conn.execute(insert_sql)
                conn.commit()
                return len(df)
            except Exception as e:
                conn.rollback()
                raise e
    
    def _get_schema(self, table_name: str) -> Dict[str, str]:
        schemas = {
            "daily": DAILY_TABLE_SCHEMA,
            "valuation": VALUATION_TABLE_SCHEMA,
            "financial": FINANCIAL_TABLE_SCHEMA,
            "stock_basic": STOCK_BASIC_TABLE_SCHEMA
        }
        return schemas.get(table_name, {})
    
    def get_stock_list(self) -> List[str]:
        with self._pool.get_connection() as conn:
            query = "SELECT ts_code FROM stock_basic WHERE status = 'L'"
            result = conn.execute(query).fetchall()
            return [row[0] for row in result]
    
    def get_table_row_count(self, table_name: str) -> int:
        with self._pool.get_connection() as conn:
            query = f"SELECT COUNT(*) FROM {table_name}"
            result = conn.execute(query).fetchone()
            return result[0] if result else 0
    
    def get_distinct_dates(self, table_name: str) -> List[str]:
        with self._pool.get_connection() as conn:
            query = f"SELECT DISTINCT trade_date FROM {table_name} ORDER BY trade_date"
            result = conn.execute(query).fetchall()
            return [str(row[0]) for row in result]
    
    def query(self, sql: str, params: Optional[List] = None) -> pd.DataFrame:
        params = params or []
        with self._pool.get_connection() as conn:
            return conn.execute(sql, params).fetchdf()
    
    def close(self):
        self._local_conn.close()
    
    def vacuum(self):
        with self._pool.get_connection() as conn:
            conn.execute("VACUUM")
            conn.commit()
    
    def analyze(self):
        with self._pool.get_connection() as conn:
            conn.execute("ANALYZE")
            conn.commit()
