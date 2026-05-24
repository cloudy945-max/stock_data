import duckdb
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict
from queue import Queue, Empty
from threading import Lock
from config import settings, DAILY_TABLE_SCHEMA, VALUATION_TABLE_SCHEMA, FINANCIAL_TABLE_SCHEMA, STOCK_BASIC_TABLE_SCHEMA


class ConnectionPool:
    def __init__(self, db_path: str, pool_size: int = 8):
        self.db_path = db_path
        self._pool_size = pool_size
        self._pool: Queue = Queue(maxsize=pool_size)
        self._init_pool()
    
    def _create_connection(self):
        conn = duckdb.connect(self.db_path, read_only=False)
        conn.execute("PRAGMA threads=1")
        return conn
    
    def _init_pool(self):
        for _ in range(self._pool_size):
            self._pool.put(self._create_connection())
    
    def get_connection(self):
        return self._pool.get(timeout=30)
    
    def return_connection(self, conn):
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
    
    @classmethod
    def _init_pool(cls):
        with cls._pool_lock:
            if cls._pool is None:
                pool_size = getattr(settings, 'CONNECTION_POOL_SIZE', 8)
                cls._pool = ConnectionPool(settings.DB_PATH, pool_size)
    
    def _ensure_dir(self):
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _execute_with_connection(self, func, *args, **kwargs):
        conn = self._pool.get_connection()
        try:
            result = func(conn, *args, **kwargs)
            return result
        finally:
            self._pool.return_connection(conn)
    
    def _execute_void(self, conn, sql, params=None):
        if params:
            conn.execute(sql, params)
        else:
            conn.execute(sql)
        conn.commit()
    
    def init_tables(self):
        def _init(conn):
            for table_name, schema in [
                ("daily", DAILY_TABLE_SCHEMA),
                ("valuation", VALUATION_TABLE_SCHEMA),
                ("financial", FINANCIAL_TABLE_SCHEMA),
                ("stock_basic", STOCK_BASIC_TABLE_SCHEMA)
            ]:
                columns = ", ".join([f"{col} {dtype}" for col, dtype in schema.items()])
                create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})"
                conn.execute(create_sql)
            
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_ts_trade ON daily (ts_code, trade_date)")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_valuation_ts_trade ON valuation (ts_code, trade_date)")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_financial_ts_end_report ON financial (ts_code, end_date, report_type)")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_stock_basic_ts ON stock_basic (ts_code)")
            
            conn.commit()
        
        self._execute_with_connection(_init)
    
    def get_latest_date(self, table_name: str, ts_code: str) -> Optional[str]:
        def _query(conn):
            query = f"SELECT MAX(trade_date) FROM {table_name} WHERE ts_code = ?"
            result = conn.execute(query, [ts_code]).fetchone()
            return str(result[0]) if result and result[0] else None
        
        return self._execute_with_connection(_query)
    
    def get_latest_financial_date(self, ts_code: str) -> Optional[str]:
        def _query(conn):
            query = "SELECT MAX(end_date) FROM financial WHERE ts_code = ?"
            result = conn.execute(query, [ts_code]).fetchone()
            return str(result[0]) if result and result[0] else None
        
        return self._execute_with_connection(_query)
    
    def insert_or_update(self, table_name: str, df: pd.DataFrame):
        if df.empty:
            return 0
        
        df = df.copy().where(pd.notnull(df), None)
        
        def _insert(conn):
            temp_table = f"temp_{table_name}_{pd.Timestamp.now().strftime('%H%M%S%f')}"
            conn.register(temp_table, df)
            
            schema = self._get_schema(table_name)
            columns = ", ".join(schema.keys())
            
            delete_sql = f"""
                DELETE FROM {table_name} 
                WHERE (ts_code, trade_date) IN (SELECT ts_code, trade_date FROM {temp_table})
            """
            
            insert_sql = f"""
                INSERT INTO {table_name} ({columns})
                SELECT {columns} FROM {temp_table}
            """
            
            conn.execute(delete_sql)
            conn.execute(insert_sql)
            conn.commit()
            
            return len(df)
        return self._execute_with_connection(_insert)
    
    def insert_or_update_financial(self, df: pd.DataFrame):
        if df.empty:
            return 0
        
        df = df.copy().where(pd.notnull(df), None)
        
        def _insert(conn):
            temp_table = f"temp_fin_{pd.Timestamp.now().strftime('%H%M%S%f')}"
            conn.register(temp_table, df)
            
            delete_sql = f"""
                DELETE FROM financial 
                WHERE (ts_code, end_date, report_type) IN (SELECT ts_code, end_date, report_type FROM {temp_table})
            """
            
            insert_sql = f"INSERT INTO financial SELECT * FROM {temp_table}"
            
            conn.execute(delete_sql)
            conn.execute(insert_sql)
            conn.commit()
            
            return len(df)
        
        return self._execute_with_connection(_insert)
    
    def insert_stock_basic(self, df: pd.DataFrame):
        if df.empty:
            return 0
        
        df = df.copy().where(pd.notnull(df), None)
        
        def _insert(conn):
            temp_table = f"temp_basic_{pd.Timestamp.now().strftime('%H%M%S%f')}"
            conn.register(temp_table, df)
            
            delete_sql = f"DELETE FROM stock_basic WHERE ts_code IN (SELECT ts_code FROM {temp_table})"
            insert_sql = f"INSERT INTO stock_basic SELECT * FROM {temp_table}"
            
            conn.execute(delete_sql)
            conn.execute(insert_sql)
            conn.commit()
            
            return len(df)
        
        return self._execute_with_connection(_insert)
    
    def _get_schema(self, table_name: str) -> Dict[str, str]:
        schemas = {
            "daily": DAILY_TABLE_SCHEMA,
            "valuation": VALUATION_TABLE_SCHEMA,
            "financial": FINANCIAL_TABLE_SCHEMA,
            "stock_basic": STOCK_BASIC_TABLE_SCHEMA
        }
        return schemas.get(table_name, {})
    
    def get_stock_list(self) -> List[str]:
        def _query(conn):
            query = "SELECT ts_code FROM stock_basic WHERE status = 'L'"
            result = conn.execute(query).fetchall()
            return [row[0] for row in result]
        
        return self._execute_with_connection(_query)
    
    def get_table_row_count(self, table_name: str) -> int:
        def _query(conn):
            query = f"SELECT COUNT(*) FROM {table_name}"
            result = conn.execute(query).fetchone()
            return result[0] if result else 0
        
        return self._execute_with_connection(_query)
    
    def get_distinct_dates(self, table_name: str) -> List[str]:
        def _query(conn):
            query = f"SELECT DISTINCT trade_date FROM {table_name} ORDER BY trade_date"
            result = conn.execute(query).fetchall()
            return [str(row[0]) for row in result]
        
        return self._execute_with_connection(_query)
    
    def query(self, sql: str, params: Optional[List] = None) -> pd.DataFrame:
        def _query(conn):
            params = params or []
            return conn.execute(sql, params).fetchdf()
        
        return self._execute_with_connection(_query)
    
    def vacuum(self):
        def _vacuum(conn):
            conn.execute("VACUUM")
            conn.commit()
        
        self._execute_with_connection(_vacuum)
    
    def analyze(self):
        def _analyze(conn):
            conn.execute("ANALYZE")
            conn.commit()
        
        self._execute_with_connection(_analyze)
    
    def close(self):
        if self._pool:
            self._pool.close_all()
            DuckDBStorage._pool = None
