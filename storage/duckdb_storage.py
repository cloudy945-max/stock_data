import os
import duckdb
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from config import settings, DAILY_TABLE_SCHEMA, VALUATION_TABLE_SCHEMA, FINANCIAL_TABLE_SCHEMA, STOCK_BASIC_TABLE_SCHEMA


class DuckDBStorage:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DB_PATH
        self._ensure_dir()
        self.conn = self._connect()
    
    def _ensure_dir(self):
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _connect(self):
        return duckdb.connect(self.db_path, read_only=False)
    
    def _create_table_if_not_exists(self, table_name: str, schema: Dict[str, str]):
        columns = ", ".join([f"{col} {dtype}" for col, dtype in schema.items()])
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {columns}
            )
        """
        self.conn.execute(create_sql)
        self.conn.commit()
    
    def _create_unique_index(self, table_name: str, columns: List[str]):
        index_name = f"idx_{table_name}_{'_'.join(columns)}"
        columns_str = ", ".join(columns)
        create_index_sql = f"""
            CREATE UNIQUE INDEX IF NOT EXISTS {index_name} 
            ON {table_name} ({columns_str})
        """
        self.conn.execute(create_index_sql)
        self.conn.commit()
    
    def init_tables(self):
        self._create_table_if_not_exists("daily", DAILY_TABLE_SCHEMA)
        self._create_unique_index("daily", ["ts_code", "trade_date"])
        
        self._create_table_if_not_exists("valuation", VALUATION_TABLE_SCHEMA)
        self._create_unique_index("valuation", ["ts_code", "trade_date"])
        
        self._create_table_if_not_exists("financial", FINANCIAL_TABLE_SCHEMA)
        self._create_unique_index("financial", ["ts_code", "end_date", "report_type"])
        
        self._create_table_if_not_exists("stock_basic", STOCK_BASIC_TABLE_SCHEMA)
        self._create_unique_index("stock_basic", ["ts_code"])
        
        self.conn.commit()
    
    def get_latest_date(self, table_name: str, ts_code: str) -> Optional[str]:
        query = f"""
            SELECT MAX(trade_date) as latest_date 
            FROM {table_name} 
            WHERE ts_code = ?
        """
        result = self.conn.execute(query, [ts_code]).fetchone()
        if result and result[0]:
            return str(result[0])
        return None
    
    def get_latest_financial_date(self, ts_code: str) -> Optional[str]:
        query = """
            SELECT MAX(end_date) as latest_date 
            FROM financial 
            WHERE ts_code = ?
        """
        result = self.conn.execute(query, [ts_code]).fetchone()
        if result and result[0]:
            return str(result[0])
        return None
    
    def insert_or_update(self, table_name: str, df: pd.DataFrame):
        if df.empty:
            return 0
        
        df = df.copy()
        df = df.where(pd.notnull(df), None)
        
        temp_table = f"temp_{table_name}_data"
        self.conn.register(temp_table, df)
        
        schema = self._get_schema(table_name)
        columns = ", ".join(schema.keys())
        placeholders = ", ".join([f"?{i+1}" for i in range(len(schema))])
        
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
            self.conn.execute(delete_sql)
            self.conn.execute(insert_sql)
            self.conn.commit()
            return len(df)
        except Exception as e:
            self.conn.rollback()
            raise e
    
    def insert_or_update_financial(self, df: pd.DataFrame):
        if df.empty:
            return 0
        
        df = df.copy()
        df = df.where(pd.notnull(df), None)
        
        temp_table = "temp_financial_data"
        self.conn.register(temp_table, df)
        
        delete_sql = """
            DELETE FROM financial 
            WHERE (ts_code, end_date, report_type) IN (
                SELECT ts_code, end_date, report_type FROM temp_financial_data
            )
        """
        
        insert_sql = """
            INSERT INTO financial 
            SELECT * FROM temp_financial_data
        """
        
        try:
            self.conn.execute(delete_sql)
            self.conn.execute(insert_sql)
            self.conn.commit()
            return len(df)
        except Exception as e:
            self.conn.rollback()
            raise e
    
    def insert_stock_basic(self, df: pd.DataFrame):
        if df.empty:
            return 0
        
        df = df.copy()
        df = df.where(pd.notnull(df), None)
        
        temp_table = "temp_stock_basic"
        self.conn.register(temp_table, df)
        
        delete_sql = """
            DELETE FROM stock_basic 
            WHERE ts_code IN (SELECT ts_code FROM temp_stock_basic)
        """
        
        insert_sql = """
            INSERT INTO stock_basic 
            SELECT * FROM temp_stock_basic
        """
        
        try:
            self.conn.execute(delete_sql)
            self.conn.execute(insert_sql)
            self.conn.commit()
            return len(df)
        except Exception as e:
            self.conn.rollback()
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
        query = "SELECT ts_code FROM stock_basic WHERE status = 'L'"
        result = self.conn.execute(query).fetchall()
        return [row[0] for row in result]
    
    def get_table_row_count(self, table_name: str) -> int:
        query = f"SELECT COUNT(*) FROM {table_name}"
        result = self.conn.execute(query).fetchone()
        return result[0] if result else 0
    
    def get_distinct_dates(self, table_name: str) -> List[str]:
        query = f"SELECT DISTINCT trade_date FROM {table_name} ORDER BY trade_date"
        result = self.conn.execute(query).fetchall()
        return [str(row[0]) for row in result]
    
    def query(self, sql: str, params: Optional[List] = None) -> pd.DataFrame:
        params = params or []
        return self.conn.execute(sql, params).fetchdf()
    
    def close(self):
        self.conn.close()
    
    def vacuum(self):
        self.conn.execute("VACUUM")
        self.conn.commit()
    
    def analyze(self):
        self.conn.execute("ANALYZE")
        self.conn.commit()
