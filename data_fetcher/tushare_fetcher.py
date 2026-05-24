import pandas as pd
import tushare as ts
from typing import Optional, List
from config import settings
from utils import get_logger, random_delay, retry_with_backoff, normalize_ts_code

logger = get_logger(__name__)


class TushareFetcher:
    def __init__(self):
        self.token = settings.TUSHARE_TOKEN
        self._init_ts()
    
    def _init_ts(self):
        if self.token:
            ts.set_token(self.token)
            self.pro_api = ts.pro_api()
        else:
            self.pro_api = None
            logger.warning("Tushare token not set, Tushare fetcher may not work")
    
    @retry_with_backoff()
    def fetch_stock_basic(self) -> pd.DataFrame:
        if not self.pro_api:
            logger.error("Tushare API not initialized")
            return pd.DataFrame()
        
        random_delay()
        try:
            df = self.pro_api.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
            df = df.rename(columns={
                'ts_code': 'ts_code',
                'symbol': 'symbol',
                'name': 'name',
                'area': 'area',
                'industry': 'industry',
                'list_date': 'list_date'
            })
            df['status'] = 'L'
            return df
        except Exception as e:
            logger.error(f"Failed to fetch stock_basic from Tushare: {e}")
            return pd.DataFrame()
    
    @retry_with_backoff()
    def fetch_daily(self, ts_code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        if not self.pro_api:
            logger.error("Tushare API not initialized")
            return pd.DataFrame()
        
        ts_code = normalize_ts_code(ts_code)
        random_delay()
        
        try:
            df = self.pro_api.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if df.empty:
                return pd.DataFrame()
            
            df = df.rename(columns={
                'ts_code': 'ts_code',
                'trade_date': 'trade_date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'pre_close': 'pre_close',
                'change': 'change',
                'pct_chg': 'pct_chg',
                'volume': 'volume',
                'amount': 'amount'
            })
            df['adj_factor'] = 1.0
            return df
        except Exception as e:
            logger.error(f"Failed to fetch daily data for {ts_code}: {e}")
            return pd.DataFrame()
    
    @retry_with_backoff()
    def fetch_adj_factor(self, ts_code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        if not self.pro_api:
            logger.error("Tushare API not initialized")
            return pd.DataFrame()
        
        ts_code = normalize_ts_code(ts_code)
        random_delay()
        
        try:
            df = self.pro_api.adj_factor(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if df.empty:
                return pd.DataFrame()
            
            df = df.rename(columns={
                'ts_code': 'ts_code',
                'trade_date': 'trade_date',
                'adj_factor': 'adj_factor'
            })
            return df
        except Exception as e:
            logger.error(f"Failed to fetch adj_factor for {ts_code}: {e}")
            return pd.DataFrame()
    
    @retry_with_backoff()
    def fetch_daily_basic(self, ts_code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        if not self.pro_api:
            logger.error("Tushare API not initialized")
            return pd.DataFrame()
        
        ts_code = normalize_ts_code(ts_code)
        random_delay()
        
        try:
            df = self.pro_api.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if df.empty:
                return pd.DataFrame()
            
            df = df.rename(columns={
                'ts_code': 'ts_code',
                'trade_date': 'trade_date',
                'pe': 'pe',
                'pe_ttm': 'pe_ttm',
                'pb': 'pb',
                'ps': 'ps',
                'ps_ttm': 'ps_ttm',
                'dv_ratio': 'dv_ratio',
                'dv_ttm': 'dv_ttm',
                'total_mv': 'total_mv',
                'circ_mv': 'circ_mv'
            })
            return df
        except Exception as e:
            logger.error(f"Failed to fetch daily_basic for {ts_code}: {e}")
            return pd.DataFrame()
    
    @retry_with_backoff()
    def fetch_income(self, ts_code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        if not self.pro_api:
            logger.error("Tushare API not initialized")
            return pd.DataFrame()
        
        ts_code = normalize_ts_code(ts_code)
        random_delay()
        
        try:
            df = self.pro_api.income(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if df.empty:
                return pd.DataFrame()
            
            df = df.rename(columns={
                'ts_code': 'ts_code',
                'ann_date': 'ann_date',
                'f_ann_date': 'f_ann_date',
                'end_date': 'end_date',
                'report_type': 'report_type',
                'basic_eps': 'basic_eps',
                'diluted_eps': 'diluted_eps',
                'total_revenue': 'total_revenue',
                'operating_revenue': 'operating_revenue',
                'profit_total': 'profit_total',
                'net_profit': 'net_profit'
            })
            return df
        except Exception as e:
            logger.error(f"Failed to fetch income for {ts_code}: {e}")
            return pd.DataFrame()
    
    @retry_with_backoff()
    def fetch_balancesheet(self, ts_code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        if not self.pro_api:
            logger.error("Tushare API not initialized")
            return pd.DataFrame()
        
        ts_code = normalize_ts_code(ts_code)
        random_delay()
        
        try:
            df = self.pro_api.balancesheet(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if df.empty:
                return pd.DataFrame()
            
            df = df.rename(columns={
                'ts_code': 'ts_code',
                'ann_date': 'ann_date',
                'f_ann_date': 'f_ann_date',
                'end_date': 'end_date',
                'report_type': 'report_type',
                'total_assets': 'total_assets',
                'total_liability': 'total_liability',
                'owner_eq': 'owner_eq'
            })
            return df
        except Exception as e:
            logger.error(f"Failed to fetch balancesheet for {ts_code}: {e}")
            return pd.DataFrame()
