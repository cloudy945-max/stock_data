import duckdb
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict
from queue import Queue, Empty
from threading import Lock
from config import settings, DAILY_TABLE_SCHEMA, VALUATION_TABLE_SCHEMA, FINANCIAL_TABLE_SCHEMA, STOCK_BASIC_TABLE_SCHEMA


class ConnectionPool:
    def __init__(self, db_path: str, pool_size: int = 4):
        self.db_path = db_path
        self._pool_size = pool_size
        self._pool: Queue = Queue(maxsize=pool_size)
        self._init_pool()

    def _create_connection(self):
        conn = duckdb.connect(self.db_path, read_only=False)
        
        if getattr(settings, 'PYTHONARM_MODE', True):
            threads = getattr(settings, 'DUCKDB_THREADS', 1)
            memory_limit = getattr(settings, 'DB_MEMORY_LIMIT', "2GB")
            conn.execute(f"PRAGMA threads={threads}")
            conn.execute(f"PRAGMA memory_limit='{memory_limit}'")
            conn.execute("PRAGMA use_external_storage=true")
        else:
            conn.execute("PRAGMA threads=1")
        
        return conn

    def _init_pool(self):
        for _ in range(self._pool_size):
            self._pool.put(self._create_connection())
<<<<<<< HEAD
=======
<<<<<<< HEAD
    
    def get_connection(self):
        return self._pool.get(timeout=60)
    
    def return_connection(self, conn):
        self._pool.put(conn)
    
=======
>>>>>>> fix-version

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = self._pool.get(timeout=30)
            yield conn
        finally:
            if conn is not None:
                self._pool.put(conn)

<<<<<<< HEAD
=======
>>>>>>> fd87bc8 (修复项目bug：数据库连接、定时任务、配置、日志)
>>>>>>> fix-version
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
<<<<<<< HEAD

=======
<<<<<<< HEAD
    
=======

>>>>>>> fd87bc8 (修复项目bug：数据库连接、定时任务、配置、日志)
>>>>>>> fix-version
    @classmethod
    def _init_pool(cls):
        with cls._pool_lock:
            if cls._pool is None:
                pool_size = getattr(settings, 'CONNECTION_POOL_SIZE', 4)
                cls._pool = ConnectionPool(settings.DB_PATH, pool_size)
<<<<<<< HEAD

    def _get_connection(self):
        return self._pool.get_connection()

    def _ensure_dir(self):
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
=======
<<<<<<< HEAD
    
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
=======

    def _get_connection(self):
        return self._pool.get_connection()

    def _ensure_dir(self):
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
>>>>>>> fix-version

    def _create_table_if_not_exists(self, table_name, schema, conn=None):
        columns = ", ".join([f"{col} {dtype}" for col, dtype in schema.items()])
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {columns}
            )
        """
        if conn:
            conn.execute(create_sql)
        else:
            with self._get_connection() as c:
                c.execute(create_sql)

    def _create_unique_index(self, table_name: str, columns: List[str], conn=None):
        index_name = f"idx_{table_name}_{'_'.join(columns)}"
        columns_str = ", ".join(columns)
        create_index_sql = f"""
            CREATE UNIQUE INDEX IF NOT EXISTS {index_name}
            ON {table_name} ({columns_str})
        """
        if conn:
            conn.execute(create_index_sql)
        else:
            with self._get_connection() as c:
                c.execute(create_index_sql)

    def init_tables(self):
        with self._get_connection() as conn:
            self._create_table_if_not_exists("daily", DAILY_TABLE_SCHEMA, conn=conn)
            self._create_unique_index("daily", ["ts_code", "trade_date"], conn=conn)

            self._create_table_if_not_exists("valuation", VALUATION_TABLE_SCHEMA, conn=conn)
            self._create_unique_index("valuation", ["ts_code", "trade_date"], conn=conn)

            self._create_table_if_not_exists("financial", FINANCIAL_TABLE_SCHEMA, conn=conn)
            self._create_unique_index("financial", ["ts_code", "end_date", "report_type"], conn=conn)

            self._create_table_if_not_exists("stock_basic", STOCK_BASIC_TABLE_SCHEMA, conn=conn)
            self._create_unique_index("stock_basic", ["ts_code"], conn=conn)

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
>>>>>>> fd87bc8 (修复项目bug：数据库连接、定时任务、配置、日志)
            temp_table = f"temp_{table_name}_{pd.Timestamp.now().strftime('%H%M%S%f')}"
            conn.register(temp_table, df)

            schema = self._get_schema(table_name)
            columns = ", ".join(schema.keys())

            delete_sql = f"""
<<<<<<< HEAD
=======
<<<<<<< HEAD
                DELETE FROM {table_name} 
                WHERE (ts_code, trade_date) IN (SELECT ts_code, trade_date FROM {temp_table})
=======
>>>>>>> fix-version
                DELETE FROM {table_name}
                WHERE (ts_code, trade_date) IN (
                    SELECT ts_code, trade_date FROM {temp_table}
                )
>>>>>>> fd87bc8 (修复项目bug：数据库连接、定时任务、配置、日志)
            """

            insert_sql = f"""
                INSERT INTO {table_name} ({columns})
                SELECT {columns} FROM {temp_table}
            """
<<<<<<< HEAD

            conn.execute(delete_sql)
            conn.execute(insert_sql)
            return len(df)

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

            conn.execute(delete_sql)
            conn.execute(insert_sql)
            return len(df)

    def insert_stock_basic(self, df: pd.DataFrame):
        if df.empty:
            return 0

        df = df.copy()
=======
<<<<<<< HEAD
            
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
    
=======

            conn.execute(delete_sql)
            conn.execute(insert_sql)
            return len(df)

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

            conn.execute(delete_sql)
            conn.execute(insert_sql)
            return len(df)

    def insert_stock_basic(self, df: pd.DataFrame):
        if df.empty:
            return 0

        df = df.copy()
>>>>>>> fix-version
        
        # ====================== 修复日期空值 ======================
        # 把空字符串、无效日期 替换成 None（数据库会存为 NULL）
        df['list_date'] = df['list_date'].replace('', None)
        df['list_date'] = pd.to_datetime(df['list_date'], errors='coerce')
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

            conn.execute(delete_sql)
            conn.execute(insert_sql)
            return len(df)

<<<<<<< HEAD
=======
>>>>>>> fd87bc8 (修复项目bug：数据库连接、定时任务、配置、日志)
>>>>>>> fix-version
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
<<<<<<< HEAD

=======
<<<<<<< HEAD
        
        return self._execute_with_connection(_query)
    
=======

>>>>>>> fd87bc8 (修复项目bug：数据库连接、定时任务、配置、日志)
>>>>>>> fix-version
    def get_table_row_count(self, table_name: str) -> int:
        def _query(conn):
            query = f"SELECT COUNT(*) FROM {table_name}"
            result = conn.execute(query).fetchone()
            return result[0] if result else 0
<<<<<<< HEAD

=======
<<<<<<< HEAD
        
        return self._execute_with_connection(_query)
    
=======

>>>>>>> fd87bc8 (修复项目bug：数据库连接、定时任务、配置、日志)
>>>>>>> fix-version
    def get_distinct_dates(self, table_name: str) -> List[str]:
        def _query(conn):
            query = f"SELECT DISTINCT trade_date FROM {table_name} ORDER BY trade_date"
            result = conn.execute(query).fetchall()
            return [str(row[0]) for row in result]
<<<<<<< HEAD

=======
<<<<<<< HEAD
        
        return self._execute_with_connection(_query)
    
=======

>>>>>>> fd87bc8 (修复项目bug：数据库连接、定时任务、配置、日志)
>>>>>>> fix-version
    def query(self, sql: str, params: Optional[List] = None) -> pd.DataFrame:
        def _query(conn):
            params = params or []
            return conn.execute(sql, params).fetchdf()
<<<<<<< HEAD

    def close(self):
        pass

    def vacuum(self):
        with self._pool.get_connection() as conn:
            conn.execute("VACUUM")

    def analyze(self):
        with self._pool.get_connection() as conn:
            conn.execute("ANALYZE")
=======
<<<<<<< HEAD
        
        return self._execute_with_connection(_query)
    
=======

    def close(self):
        pass

>>>>>>> fd87bc8 (修复项目bug：数据库连接、定时任务、配置、日志)
    def vacuum(self):
        def _vacuum(conn):
            conn.execute("VACUUM")
<<<<<<< HEAD
            conn.commit()
        
        self._execute_with_connection(_vacuum)
    
=======

>>>>>>> fd87bc8 (修复项目bug：数据库连接、定时任务、配置、日志)
    def analyze(self):
        def _analyze(conn):
            conn.execute("ANALYZE")
<<<<<<< HEAD
            conn.commit()
        
        self._execute_with_connection(_analyze)
    
    def close(self):
        if self._pool:
            self._pool.close_all()
            DuckDBStorage._pool = None
=======
>>>>>>> fd87bc8 (修复项目bug：数据库连接、定时任务、配置、日志)
>>>>>>> fix-version
