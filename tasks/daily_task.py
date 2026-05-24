import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional
from config import settings
from storage import DuckDBStorage
from data_fetcher import TushareFetcher, AKShareFetcher
from utils import get_logger, standardize_daily_data, standardize_valuation_data, standardize_financial_data, random_delay

logger = get_logger(__name__)


class DailyUpdateTask:
    def __init__(self):
        self.storage = DuckDBStorage()
        self.tushare_fetcher = TushareFetcher()
        self.akshare_fetcher = AKShareFetcher()
        
        self._concurrent_workers = settings.MAX_CONCURRENT
        if getattr(settings, 'PYTHONARM_MODE', False):
            self._concurrent_workers = min(self._concurrent_workers, 2)
            logger.info(f"[ARM MODE] Running in ARM NAS mode, concurrency limited to {self._concurrent_workers}")
    
    def _should_update_financial(self) -> bool:
        if settings.FINANCIAL_UPDATE_FREQ == "daily":
            return True
        
        today = datetime.now()
        weekday = today.weekday()
        
        if settings.FINANCIAL_UPDATE_FREQ == "weekly":
            return weekday == settings.FINANCIAL_WEEKLY_DAY
        
        if settings.FINANCIAL_UPDATE_FREQ == "monthly":
            return today.day >= 20
        
        return False
    
    def update_stock_basic(self) -> int:
        logger.info("Starting to update stock basic info")
        
        random_delay()
        
        dfs = []
        
        if settings.TUSHARE_ENABLED:
            try:
                df = self.tushare_fetcher.fetch_stock_basic()
                if not df.empty:
                    dfs.append(df)
                    logger.info(f"Fetched {len(df)} stocks from Tushare")
            except Exception as e:
                logger.warning(f"Tushare stock_basic failed: {e}")
        
        if settings.AKShare_ENABLED and not dfs:
            try:
                df = self.akshare_fetcher.fetch_stock_basic()
                if not df.empty:
                    dfs.append(df)
                    logger.info(f"Fetched {len(df)} stocks from AKShare")
            except Exception as e:
                logger.warning(f"AKShare stock_basic failed: {e}")
        
        if not dfs:
            logger.warning("No stock basic data fetched")
            return 0
        
        combined_df = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=['ts_code'])
        inserted = self.storage.insert_stock_basic(combined_df)
        logger.info(f"Updated {inserted} stock basic records")
        
        return inserted
    
    def update_daily_data(self, ts_code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[str, int, str]:
        ts_code_clean = str(ts_code).strip()
        
        try:
            latest_date = self.storage.get_latest_date("daily", ts_code_clean)
            
            if start_date is None and latest_date:
                start_date = latest_date
            
            df = pd.DataFrame()
            data_source = None
            
            if settings.TUSHARE_ENABLED:
                try:
                    df = self.tushare_fetcher.fetch_daily(ts_code, start_date, end_date)
                    if not df.empty:
                        data_source = "Tushare"
                        logger.debug(f"[{ts_code_clean}] Got {len(df)} records from Tushare")
                except Exception as e:
                    logger.warning(f"[{ts_code_clean}] Tushare daily failed: {e}")
            
            if df.empty and settings.AKShare_ENABLED:
                try:
                    df = self.akshare_fetcher.fetch_daily(ts_code, start_date, end_date)
                    if not df.empty:
                        data_source = "AKShare"
                        logger.debug(f"[{ts_code_clean}] Got {len(df)} records from AKShare")
                except Exception as e:
                    logger.warning(f"[{ts_code_clean}] AKShare daily failed: {e}")
            
            if df.empty:
                return (ts_code_clean, 0, "no_data")
            
            df = standardize_daily_data(df)
            
            if start_date:
                df = df[df['trade_date'] > start_date]
            
            if df.empty:
                return (ts_code_clean, 0, "no_new_data")
            
            inserted = self.storage.insert_or_update("daily", df)
            logger.info(f"[{ts_code_clean}] Inserted {inserted} daily records from {data_source}")
            return (ts_code_clean, inserted, "success")
        
        except Exception as e:
            logger.error(f"[{ts_code_clean}] Error updating daily data: {e}", exc_info=True)
            return (ts_code_clean, 0, str(e))
    
    def update_valuation_data(self, ts_code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[str, int, str]:
        ts_code_clean = str(ts_code).strip()
        
        try:
            latest_date = self.storage.get_latest_date("valuation", ts_code_clean)
            
            if start_date is None and latest_date:
                start_date = latest_date
            
            df = pd.DataFrame()
            
            if settings.AKShare_ENABLED:
                try:
                    random_delay()
                    df = self.akshare_fetcher.fetch_valuation(ts_code, start_date, end_date)
                    if not df.empty:
                        logger.debug(f"[{ts_code_clean}] Got {len(df)} valuation records from AKShare")
                except Exception as e:
                    logger.warning(f"[{ts_code_clean}] AKShare valuation failed: {e}")
            
            if df.empty:
                return (ts_code_clean, 0, "no_data")
            
            df = standardize_valuation_data(df)
            
            if start_date:
                df = df[df['trade_date'] > start_date]
            
            if df.empty:
                return (ts_code_clean, 0, "no_new_data")
            
            inserted = self.storage.insert_or_update("valuation", df)
            logger.info(f"[{ts_code_clean}] Inserted {inserted} valuation records")
            return (ts_code_clean, inserted, "success")
        
        except Exception as e:
            logger.error(f"[{ts_code_clean}] Error updating valuation data: {e}", exc_info=True)
            return (ts_code_clean, 0, str(e))
    
    def update_financial_data(self, ts_code: str) -> Tuple[str, int, str]:
        ts_code_clean = str(ts_code).strip()
        
        try:
            latest_date = self.storage.get_latest_financial_date(ts_code_clean)
            
            dfs = []
            
            if settings.AKShare_ENABLED:
                try:
                    random_delay()
                    yearly_df = self.akshare_fetcher.fetch_financial_report(ts_code, "yearly")
                    if not yearly_df.empty:
                        dfs.append(yearly_df)
                        logger.debug(f"[{ts_code_clean}] Got {len(yearly_df)} yearly records from AKShare")
                    
                    random_delay()
                    quarterly_df = self.akshare_fetcher.fetch_financial_report(ts_code, "quarterly")
                    if not quarterly_df.empty:
                        dfs.append(quarterly_df)
                        logger.debug(f"[{ts_code_clean}] Got {len(quarterly_df)} quarterly records from AKShare")
                except Exception as e:
                    logger.warning(f"[{ts_code_clean}] AKShare financial failed: {e}")
            
            if not dfs:
                return (ts_code_clean, 0, "no_data")
            
            combined_df = pd.concat(dfs, ignore_index=True)
            combined_df = standardize_financial_data(combined_df)
            
            if latest_date:
                combined_df = combined_df[combined_df['end_date'] > latest_date]
            
            if combined_df.empty:
                return (ts_code_clean, 0, "no_new_data")
            
            inserted = self.storage.insert_or_update_financial(combined_df)
            logger.info(f"[{ts_code_clean}] Inserted {inserted} financial records")
            return (ts_code_clean, inserted, "success")
        
        except Exception as e:
            logger.error(f"[{ts_code_clean}] Error updating financial data: {e}", exc_info=True)
            return (ts_code_clean, 0, str(e))
    
    def run_daily_update(self, stock_list: List[str] = None) -> Dict[str, dict]:
        logger.info("=" * 60)
        logger.info("Starting daily update task")
        if getattr(settings, 'PYTHONARM_MODE', False):
            logger.info(f"[ARM MODE] Concurrency limited to {self._concurrent_workers}")
        logger.info(f"Financial update frequency: {settings.FINANCIAL_UPDATE_FREQ}")
        logger.info(f"Should update financial today: {self._should_update_financial()}")
        logger.info("=" * 60)
        
        if stock_list is None:
            stock_list = self.storage.get_stock_list()
        
        if not stock_list:
            logger.warning("No stocks to update")
            return {}
        
        results = {
            'daily': {'success': 0, 'failed': 0, 'no_data': 0, 'total_records': 0, 'failed_stocks': []},
            'valuation': {'success': 0, 'failed': 0, 'no_data': 0, 'total_records': 0, 'failed_stocks': []},
            'financial': {'success': 0, 'failed': 0, 'no_data': 0, 'total_records': 0, 'failed_stocks': []}
        }
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        if settings.UPDATE_DAILY:
            logger.info(f"[DAILY] Updating daily data for {len(stock_list)} stocks")
            
            with ThreadPoolExecutor(max_workers=self._concurrent_workers) as executor:
                futures = {executor.submit(self.update_daily_data, ts_code, None, end_date): ts_code for ts_code in stock_list}
                
                for future in as_completed(futures):
                    try:
                        ts_code, count, status = future.result()
                        if status == "success":
                            results['daily']['success'] += 1
                            results['daily']['total_records'] += count
                        elif status in ["no_data", "no_new_data"]:
                            results['daily']['no_data'] += 1
                        else:
                            results['daily']['failed'] += 1
                            results['daily']['failed_stocks'].append(ts_code)
                    except Exception as e:
                        logger.error(f"Future result exception: {e}")
            
            logger.info(f"[DAILY] Completed: {results['daily']['success']} success, {results['daily']['failed']} failed, {results['daily']['no_data']} no_data, {results['daily']['total_records']} records")
        
        if settings.UPDATE_VALUATION:
            logger.info(f"[VALUATION] Updating valuation data for {len(stock_list)} stocks")
            
            with ThreadPoolExecutor(max_workers=self._concurrent_workers) as executor:
                futures = {executor.submit(self.update_valuation_data, ts_code, None, end_date): ts_code for ts_code in stock_list}
                
                for future in as_completed(futures):
                    try:
                        ts_code, count, status = future.result()
                        if status == "success":
                            results['valuation']['success'] += 1
                            results['valuation']['total_records'] += count
                        elif status in ["no_data", "no_new_data"]:
                            results['valuation']['no_data'] += 1
                        else:
                            results['valuation']['failed'] += 1
                            results['valuation']['failed_stocks'].append(ts_code)
                    except Exception as e:
                        logger.error(f"Future result exception: {e}")
            
            logger.info(f"[VALUATION] Completed: {results['valuation']['success']} success, {results['valuation']['failed']} failed, {results['valuation']['no_data']} no_data, {results['valuation']['total_records']} records")
        
        if settings.UPDATE_FINANCIAL and self._should_update_financial():
            logger.info(f"[FINANCIAL] Updating financial data for {len(stock_list)} stocks")
            
            with ThreadPoolExecutor(max_workers=self._concurrent_workers) as executor:
                futures = {executor.submit(self.update_financial_data, ts_code): ts_code for ts_code in stock_list}
                
                for future in as_completed(futures):
                    try:
                        ts_code, count, status = future.result()
                        if status == "success":
                            results['financial']['success'] += 1
                            results['financial']['total_records'] += count
                        elif status in ["no_data", "no_new_data"]:
                            results['financial']['no_data'] += 1
                        else:
                            results['financial']['failed'] += 1
                            results['financial']['failed_stocks'].append(ts_code)
                    except Exception as e:
                        logger.error(f"Future result exception: {e}")
            
            logger.info(f"[FINANCIAL] Completed: {results['financial']['success']} success, {results['financial']['failed']} failed, {results['financial']['no_data']} no_data, {results['financial']['total_records']} records")
        elif settings.UPDATE_FINANCIAL:
            logger.info("[FINANCIAL] Skipped - not scheduled for today")
        
        logger.info("=" * 60)
        logger.info("Daily update task completed")
        logger.info("=" * 60)
        
        self.storage.close()
        return results
    
    def run_history_fetch(self, stock_list: List[str] = None, start_date: str = "20000101", end_date: str = None) -> Dict[str, dict]:
        logger.info("=" * 60)
        logger.info(f"Starting history fetch task: {start_date} to {end_date or 'now'}")
        if getattr(settings, 'PYTHONARM_MODE', False):
            logger.info(f"[ARM MODE] Concurrency limited to {self._concurrent_workers}")
        logger.info("=" * 60)
        
        if stock_list is None:
            stock_list = self.storage.get_stock_list()
        
        if not stock_list:
            logger.warning("No stocks to fetch")
            return {}
        
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        
        results = {
            'daily': {'success': 0, 'failed': 0, 'total_records': 0, 'failed_stocks': []},
            'valuation': {'success': 0, 'failed': 0, 'total_records': 0, 'failed_stocks': []},
            'financial': {'success': 0, 'failed': 0, 'total_records': 0, 'failed_stocks': []}
        }
        
        if settings.UPDATE_DAILY:
            logger.info(f"[DAILY] Fetching historical daily data for {len(stock_list)} stocks")
            
            with ThreadPoolExecutor(max_workers=self._concurrent_workers) as executor:
                futures = {executor.submit(self.update_daily_data, ts_code, start_date, end_date): ts_code for ts_code in stock_list}
                
                for future in as_completed(futures):
                    try:
                        ts_code, count, status = future.result()
                        if status == "success":
                            results['daily']['success'] += 1
                            results['daily']['total_records'] += count
                        else:
                            results['daily']['failed'] += 1
                            results['daily']['failed_stocks'].append(ts_code)
                    except Exception as e:
                        logger.error(f"Future result exception: {e}")
            
            logger.info(f"[DAILY] Completed: {results['daily']['success']} success, {results['daily']['failed']} failed, {results['daily']['total_records']} records")
        
        if settings.UPDATE_VALUATION:
            logger.info(f"[VALUATION] Fetching historical valuation data for {len(stock_list)} stocks")
            
            with ThreadPoolExecutor(max_workers=self._concurrent_workers) as executor:
                futures = {executor.submit(self.update_valuation_data, ts_code, start_date, end_date): ts_code for ts_code in stock_list}
                
                for future in as_completed(futures):
                    try:
                        ts_code, count, status = future.result()
                        if status == "success":
                            results['valuation']['success'] += 1
                            results['valuation']['total_records'] += count
                        else:
                            results['valuation']['failed'] += 1
                            results['valuation']['failed_stocks'].append(ts_code)
                    except Exception as e:
                        logger.error(f"Future result exception: {e}")
            
            logger.info(f"[VALUATION] Completed: {results['valuation']['success']} success, {results['valuation']['failed']} failed, {results['valuation']['total_records']} records")
        
        if settings.UPDATE_FINANCIAL:
            logger.info(f"[FINANCIAL] Fetching historical financial data for {len(stock_list)} stocks")
            
            with ThreadPoolExecutor(max_workers=self._concurrent_workers) as executor:
                futures = {executor.submit(self.update_financial_data, ts_code): ts_code for ts_code in stock_list}
                
                for future in as_completed(futures):
                    try:
                        ts_code, count, status = future.result()
                        if status == "success":
                            results['financial']['success'] += 1
                            results['financial']['total_records'] += count
                        else:
                            results['financial']['failed'] += 1
                            results['financial']['failed_stocks'].append(ts_code)
                    except Exception as e:
                        logger.error(f"Future result exception: {e}")
            
            logger.info(f"[FINANCIAL] Completed: {results['financial']['success']} success, {results['financial']['failed']} failed, {results['financial']['total_records']} records")
        
        logger.info("=" * 60)
        logger.info("History fetch task completed")
        logger.info("=" * 60)
        
        self.storage.close()
        return results
