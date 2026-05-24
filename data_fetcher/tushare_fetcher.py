import pandas as pd
import tushare as ts
from typing import Optional
from config import settings
from utils import get_logger, random_delay, retry_with_backoff, normalize_ts_code

logger = get_logger(__name__)


class TushareFetcher:
    def __init__(self):
        self.token = settings.TUSHARE_TOKEN
        self._data_source = "Tushare"
        self._init_ts()
    
    def _init_ts(self):
        if self.token:
            ts.set_token(self.token)
            self.pro_api = ts.pro_api()
            logger.info("[Tushare] API initialized successfully")
        else:
            self.pro_api = None
            logger.warning("[Tushare] Token not set, Tushare fetcher may not work")
    
    @retry_with_backoff()
    def fetch_stock_basic(self) -> pd.DataFrame:
        if not self.pro_api:
            logger.error("[Tushare] API not initialized")
            return pd.DataFrame()
        
        random_delay()
        try:
            df = self.pro_api.stock_basic(exchange='', list_status='L', 
                                          fields='ts_code,symbol,name,area,industry,list_date')
            if df.empty:
                logger.warning("[Tushare] stock_basic returned empty")
                return pd.DataFrame()
            
            df = df.rename(columns={
                'ts_code': 'ts_code',
                'symbol': 'symbol',
                'name': 'name',
                'area': 'area',
                'industry': 'industry',
                'list_date': 'list_date'
            })
            df['status'] = 'L'
            
            logger.info(f"[Tushare] Fetched {len(df)} stocks from stock_basic")
            return df
        except Exception as e:
            logger.error(f"[Tushare] Failed to fetch stock_basic: {e}")
            return pd.DataFrame()
    
    @retry_with_backoff()
    def fetch_daily(self, ts_code: str, start_date: Optional[str] = None, 
                    end_date: Optional[str] = None) -> pd.DataFrame:
        if not self.pro_api:
            logger.error("[Tushare] API not initialized")
            return pd.DataFrame()
        
        ts_code = normalize_ts_code(ts_code)
        if not ts_code:
            logger.warning(f"[Tushare] Invalid ts_code: {ts_code}")
            return pd.DataFrame()
        
        random_delay()
        
        try:
            df = self.pro_api.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if df.empty:
                logger.debug(f"[Tushare] No daily data for {ts_code}")
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
                'vol': 'volume',
                'amount': 'amount'
            })
            df['adj_factor'] = 1.0
            
            logger.debug(f"[Tushare] Got {len(df)} daily records for {ts_code}")
            return df
        except Exception as e:
            logger.error(f"[Tushare] Failed to fetch daily for {ts_code}: {e}")
            return pd.DataFrame()
    
    @retry_with_backoff()
    def fetch_adj_factor(self, ts_code: str, start_date: Optional[str] = None, 
                        end_date: Optional[str] = None) -> pd.DataFrame:
        if not self.pro_api:
            logger.error("[Tushare] API not initialized")
            return pd.DataFrame()
        
        ts_code = normalize_ts_code(ts_code)
        if not ts_code:
            logger.warning(f"[Tushare] Invalid ts_code for adj_factor: {ts_code}")
            return pd.DataFrame()
        
        random_delay()
        
        try:
            df = self.pro_api.adj_factor(ts_code=ts_code, start_date=start_date, end_date=end_date)
            if df.empty:
                logger.debug(f"[Tushare] No adj_factor data for {ts_code}")
                return pd.DataFrame()
            
            df = df.rename(columns={
                'ts_code': 'ts_code',
                'trade_date': 'trade_date',
                'adj_factor': 'adj_factor'
            })
            
            logger.debug(f"[Tushare] Got {len(df)} adj_factor records for {ts_code}")
            return df
        except Exception as e:
            logger.error(f"[Tushare] Failed to fetch adj_factor for {ts_code}: {e}")
            return pd.DataFrame()
