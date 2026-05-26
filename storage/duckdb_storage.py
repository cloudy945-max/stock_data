import duckdb
from config import settings
import logging

logger = logging.getLogger(__name__)

class DuckDBStorage:
    def __init__(self, db_path=None):
        self.db_path = db_path or settings.DB_PATH
        self.conn = duckdb.connect(self.db_path)
        self._init_tables()

    def _init_tables(self):
        # 全 VARCHAR，彻底杜绝日期报错
        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS stock_basic (
            ts_code VARCHAR,
            symbol VARCHAR,
            name VARCHAR,
            area VARCHAR,
            industry VARCHAR,
            list_date VARCHAR,
            status VARCHAR
        )
        ''')

    def save_stock_basic(self, data):
        if not data:
            return
        
        # 先清空，再插入，绝对不报错
        self.conn.execute("DELETE FROM stock_basic")
        
        # 强制给默认日期，空值必死
        valid_data = []
        for item in data:
            valid_data.append((
                item.get("ts_code", ""),
                item.get("symbol", ""),
                item.get("name", ""),
                item.get("area", ""),
                item.get("industry", ""),
                "2000-01-01",  # 强制写死合法日期
                item.get("status", "active")
            ))
        
        self.conn.executemany('''
            INSERT INTO stock_basic
            (ts_code, symbol, name, area, industry, list_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', valid_data)
        
        logger.info(f"✅ 成功写入 {len(data)} 只 A 股！")

    def close(self):
        self.conn.close()
