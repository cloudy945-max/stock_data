import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
from config import settings
from storage import DuckDBStorage
from data_fetcher import TushareFetcher, AKShareFetcher
from utils import get_logger, standardize_daily_data, standardize_valuation_data, standardize_financial_data

logger = get_logger(__name__)


class DailyUpdateTask:
    def __init__(self):
        self.storage = DuckDBStorage()
        self.tushare_fetcher = TushareFetcher()
        self.akshare_fetcher = AKShareFetcher()
    
    def update_stock_basic(self) -> int:
        logger.info("Starting to update stock basic info")
        
        dfs = []
        
        if settings.TUSHARE_ENABLED:
            df = self.tushare_fetcher.fetch_stock_basic()
            if not df.empty:
                dfs.append(df)
                logger.info(f"Fetched {len(df)} stocks from Tushare")
        
        if settings.AKShare_ENABLED and not dfs:
            df = self.akshare_fetcher.fetch_stock_basic()
            if not df.empty:
                dfs.append(df)
                logger.info(f"Fetched {len(df)} stocks from AKShare")
        
        if not dfs:
            logger.warning("No stock basic data fetched")
            return 0
        
        combined_df = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=['ts_code'])
        inserted = self.storage.insert_stock_basic(combined_df)
        logger.info(f"Updated {inserted} stock basic records")
        
        return inserted
    
    def update_daily_data(self, ts_code: str, start_date: str = None, end_date: str = None) -> Tuple[str, int, str]:
        try:
            latest_date = self.storage.get_latest_date("daily", ts_code)
            
            if start_date is None and latest_date:
                start_date = latest_date
            
            dfs = []
            
            if settings.TUSHARE_ENABLED:
                df = self.tushare_fetcher.fetch_daily(ts_code, start_date, end_date)
                if not df.empty:
                    dfs.append(df)
            
            if settings.AKShare_ENABLED:
                df = self.akshare_fetcher.fetch_daily(ts_code, start_date, end_date)
                if not df.empty:
                    dfs.append(df)
            
            if not dfs:
                return (ts_code, 0, "no_data")
            
            combined_df = pd.concat(dfs, ignore_index=True)
            combined_df = standardize_daily_data(combined_df)
            
            if start_date:
                combined_df = combined_df[combined_df['trade_date'] > start_date]
            
            if combined_df.empty:
                return (ts_code, 0, "no_new_data")
            
            inserted = self.storage.insert_or_update("daily", combined_df)
            return (ts_code, inserted, "success")
        
        except Exception as e:
            logger.error(f"Error updating daily data for {ts_code}: {e}")
            return (ts_code, 0, str(e))
    
    def update_valuation_data(self, ts_code: str, start_date: str = None, end_date: str = None) -> Tuple[str, int, str]:
        try:
            latest_date = self.storage.get_latest_date("valuation", ts_code)
            
            if start_date is None and latest_date:
                start_date = latest_date
            
            df = pd.DataFrame()
            
            if settings.AKShare_ENABLED:
                df = self.akshare_fetcher.fetch_valuation(ts_code, start_date, end_date)
            
            if settings.TUSHARE_ENABLED and df.empty:
                df = self.tushare_fetcher.fetch_daily_basic(ts_code, start_date, end_date)
            
            if df.empty:
                return (ts_code, 0, "no_data")
            
            df = standardize_valuation_data(df)
            
            if start_date:
                df = df[df['trade_date'] > start_date]
            
            if df.empty:
                return (ts_code, 0, "no_new_data")
            
            inserted = self.storage.insert_or_update("valuation", df)
            return (ts_code, inserted, "success")
        
        except Exception as e:
            logger.error(f"Error updating valuation for {ts_code}: {e}")
            return (ts_code, 0, str(e))
    
    def update_financial_data(self, ts_code: str) -> Tuple[str, int, str]:
        try:
            latest_date = self.storage.get_latest_financial_date(ts_code)
            
            dfs = []
            
            if settings.AKShare_ENABLED:
                yearly_df = self.akshare_fetcher.fetch_financial_report(ts_code, "yearly")
                if not yearly_df.empty:
                    dfs.append(yearly_df)
                
                quarterly_df = self.akshare_fetcher.fetch_financial_report(ts_code, "quarterly")
                if not quarterly_df.empty:
                    dfs.append(quarterly_df)
            
            if settings.TUSHARE_ENABLED:
                income_df = self.tushare_fetcher.fetch_income(ts_code)
                if not income_df.empty:
                    dfs.append(income_df)
                
                balance_df = self.tushare_fetcher.fetch_balancesheet(ts_code)
                if not balance_df.empty:
                    dfs.append(balance_df)
            
            if not dfs:
                return (ts_code, 0, "no_data")
            
            combined_df = pd.concat(dfs, ignore_index=True)
            combined_df = standardize_financial_data(combined_df)
            
            if latest_date:
                combined_df = combined_df[combined_df['end_date'] > latest_date]
            
            if combined_df.empty:
                return (ts_code, 0, "no_new_data")
            
            inserted = self.storage.insert_or_update_financial(combined_df)
            return (ts_code, inserted, "success")
        
        except Exception as e:
            logger.error(f"Error updating financial data for {ts_code}: {e}")
            return (ts_code, 0, str(e))
    
    def run_daily_update(self, stock_list: List[str] = None) -> Dict[str, dict]:
        logger.info("Starting daily update task")
        
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
            logger.info(f"Updating daily data for {len(stock_list)} stocks")
            
            with ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT) as executor:
                futures = {executor.submit(self.update_daily_data, ts_code, None, end_date): ts_code for ts_code in stock_list}
                
                for future in as_completed(futures):
                    ts_code, count, status = future.result()
                    if status == "success":
                        results['daily']['success'] += 1
                        results['daily']['total_records'] += count
                    elif status in ["no_data", "no_new_data"]:
                        results['daily']['no_data'] += 1
                    else:
                        results['daily']['failed'] += 1
                        results['daily']['failed_stocks'].append(ts_code)
            
            logger.info(f"Daily update completed: {results['daily']['success']} success, {results['daily']['failed']} failed, {results['daily']['no_data']} no data")
        
        if settings.UPDATE_VALUATION:
            logger.info(f"Updating valuation data for {len(stock_list)} stocks")
            
            with ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT) as executor:
                futures = {executor.submit(self.update_valuation_data, ts_code, None, end_date): ts_code for ts_code in stock_list}
                
                for future in as_completed(futures):
                    ts_code, count, status = future.result()
                    if status == "success":
                        results['valuation']['success'] += 1
                        results['valuation']['total_records'] += count
                    elif status in ["no_data", "no_new_data"]:
                        results['valuation']['no_data'] += 1
                    else:
                        results['valuation']['failed'] += 1
                        results['valuation']['failed_stocks'].append(ts_code)
            
            logger.info(f"Valuation update completed: {results['valuation']['success']} success, {results['valuation']['failed']} failed, {results['valuation']['no_data']} no data")
        
        if settings.UPDATE_FINANCIAL:
            logger.info(f"Updating financial data for {len(stock_list)} stocks")
            
            with ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT) as executor:
                futures = {executor.submit(self.update_financial_data, ts_code): ts_code for ts_code in stock_list}
                
                for future in as_completed(futures):
                    ts_code, count, status = future.result()
                    if status == "success":
                        results['financial']['success'] += 1
                        results['financial']['total_records'] += count
                    elif status in ["no_data", "no_new_data"]:
                        results['financial']['no_data'] += 1
                    else:
                        results['financial']['failed'] += 1
                        results['financial']['failed_stocks'].append(ts_code)
            
            logger.info(f"Financial update completed: {results['financial']['success']} success, {results['financial']['failed']} failed, {results['financial']['no_data']} no data")
        
        self.storage.close()
        return results
    
    def run_history_fetch(self, stock_list: List[str] = None, start_date: str = "20000101", end_date: str = None) -> Dict[str, dict]:
        logger.info("Starting history fetch task")
        
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
            logger.info(f"Fetching historical daily data for {len(stock_list)} stocks")
            
            with ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT) as executor:
                futures = {executor.submit(self.update_daily_data, ts_code, start_date, end_date): ts_code for ts_code in stock_list}
                
                for future in as_completed(futures):
                    ts_code, count, status = future.result()
                    if status == "success":
                        results['daily']['success'] += 1
                        results['daily']['total_records'] += count
                    else:
                        results['daily']['failed'] += 1
                        results['daily']['failed_stocks'].append(ts_code)
            
            logger.info(f"Historical daily fetch completed: {results['daily']['success']} success, {results['daily']['failed']} failed")
        
        if settings.UPDATE_VALUATION:
            logger.info(f"Fetching historical valuation data for {len(stock_list)} stocks")
            
            with ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT) as executor:
                futures = {executor.submit(self.update_valuation_data, ts_code, start_date, end_date): ts_code for ts_code in stock_list}
                
                for future in as_completed(futures):
                    ts_code, count, status = future.result()
                    if status == "success":
                        results['valuation']['success'] += 1
                        results['valuation']['total_records'] += count
                    else:
                        results['valuation']['failed'] += 1
                        results['valuation']['failed_stocks'].append(ts_code)
            
            logger.info(f"Historical valuation fetch completed: {results['valuation']['success']} success, {results['valuation']['failed']} failed")
        
        if settings.UPDATE_FINANCIAL:
            logger.info(f"Fetching historical financial data for {len(stock_list)} stocks")
            
            with ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT) as executor:
                futures = {executor.submit(self.update_financial_data, ts_code): ts_code for ts_code in stock_list}
                
                for future in as_completed(futures):
                    ts_code, count, status = future.result()
                    if status == "success":
                        results['financial']['success'] += 1
                        results['financial']['total_records'] += count
                    else:
                        results['financial']['failed'] += 1
                        results['financial']['failed_stocks'].append(ts_code)
            
            logger.info(f"Historical financial fetch completed: {results['financial']['success']} success, {results['financial']['failed']} failed")
        
        self.storage.close()
        return results
