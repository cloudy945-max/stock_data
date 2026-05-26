import logging
import pandas as pd
from data_fetcher.tushare_fetcher import TushareFetcher
from data_fetcher.akshare_fetcher import AKShareFetcher
from storage import DuckDBStorage

logger = logging.getLogger(__name__)

class DailyUpdateTask:
    def __init__(self):
        self.tushare = TushareFetcher()
        self.akshare = AKShareFetcher()
        self.storage = DuckDBStorage()

    def update_stock_basic(self):
        logger.info("Starting to update stock basic info")
        
        data = None
        try:
            data = self.tushare.fetch_stock_basic()
        except Exception as e:
            logger.error(f"Tushare failed: {e}")
        
        # 从 AKShare 获取数据
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            try:
                data = self.akshare.fetch_stock_basic()
            except Exception as e:
                logger.error(f"AKShare failed: {e}")
        
        # 最终判断是否有数据
        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            logger.warning("No stock basic data fetched")
            return
        
        # 转换成字典列表
        if isinstance(data, pd.DataFrame):
            data = data.to_dict('records')
        
        logger.info(f"Fetched {len(data)} stocks from source")
        
        # 保存数据库
        self.storage.save_stock_basic(data)
        logger.info("Stock basic info updated successfully")

    def run_daily_update(self):
        logger.info("Starting daily update task")
        logger.warning("No stocks to update")
        return

    def close(self):
        self.storage.close()
