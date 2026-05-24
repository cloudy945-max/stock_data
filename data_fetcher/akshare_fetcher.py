import pandas as pd
import akshare as ak
import random
from typing import Optional
from config import settings, USER_AGENT_POOL
from utils import get_logger, random_delay, retry_with_backoff, normalize_ts_code

logger = get_logger(__name__)


class AKShareFetcher:
    def __init__(self):
        self._setup_session()
    
    def _setup_session(self):
        if settings.PROXY_ENABLED and settings.PROXY_URL:
            ak.set_proxy(settings.PROXY_URL)
    
    def _set_random_user_agent(self):
        ak.headers = {"User-Agent": random.choice(USER_AGENT_POOL)}
    
    @retry_with_backoff()
    def fetch_stock_basic(self) -> pd.DataFrame:
        random_delay()
        self._set_random_user_agent()
        
        try:
            df = ak.stock_zh_a_spot()
            if df.empty:
                logger.warning("AKShare stock_zh_a_spot returned empty")
                return pd.DataFrame()
            
            df = df.rename(columns={
                '代码': 'symbol',
                '名称': 'name',
                '最新价': 'close',
                '涨跌幅': 'pct_chg',
                '成交量': 'volume',
                '成交额': 'amount'
            })
            
            df['ts_code'] = df['symbol'].apply(normalize_ts_code)
            df['status'] = 'L'
            df['area'] = ''
            df['industry'] = ''
            df['list_date'] = ''
            
            return df[['ts_code', 'symbol', 'name', 'area', 'industry', 'list_date', 'status']]
        except Exception as e:
            logger.error(f"Failed to fetch stock_basic from AKShare: {e}")
            return pd.DataFrame()
    
    @retry_with_backoff()
    def fetch_daily(self, ts_code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        ts_code = normalize_ts_code(ts_code)
        symbol = ts_code.split('.')[0]
        
        random_delay()
        self._set_random_user_agent()
        
        try:
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
            if df.empty:
                return pd.DataFrame()
            
            df = df.rename(columns={
                '日期': 'trade_date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '涨跌幅': 'pct_chg',
                '涨跌额': 'change',
                '换手率': 'turnover_rate'
            })
            
            df['ts_code'] = ts_code
            df['pre_close'] = df['close'].shift(1)
            df['adj_factor'] = 1.0
            
            df = df[['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 
                     'pre_close', 'change', 'pct_chg', 'volume', 'amount', 'adj_factor']]
            return df
        except Exception as e:
            logger.error(f"Failed to fetch daily data for {ts_code}: {e}")
            return pd.DataFrame()
    
    @retry_with_backoff()
    def fetch_valuation(self, ts_code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        ts_code = normalize_ts_code(ts_code)
        symbol = ts_code.split('.')[0]
        
        random_delay()
        self._set_random_user_agent()
        
        try:
            df = ak.stock_a_indicator_lg(symbol=symbol)
            if df.empty:
                return pd.DataFrame()
            
            df = df.rename(columns={
                '日期': 'trade_date',
                '市盈率': 'pe',
                '市盈率TTM': 'pe_ttm',
                '市净率': 'pb',
                '市销率': 'ps',
                '市销率TTM': 'ps_ttm',
                '股息率': 'dv_ratio',
                '股息率TTM': 'dv_ttm',
                '总市值': 'total_mv',
                '流通市值': 'circ_mv'
            })
            
            df['ts_code'] = ts_code
            
            df = df[['ts_code', 'trade_date', 'pe', 'pe_ttm', 'pb', 'ps', 
                     'ps_ttm', 'dv_ratio', 'dv_ttm', 'total_mv', 'circ_mv']]
            return df
        except Exception as e:
            logger.error(f"Failed to fetch valuation for {ts_code}: {e}")
            return pd.DataFrame()
    
    @retry_with_backoff()
    def fetch_financial_report(self, ts_code: str, report_type: str = "yearly") -> pd.DataFrame:
        ts_code = normalize_ts_code(ts_code)
        symbol = ts_code.split('.')[0]
        
        random_delay()
        self._set_random_user_agent()
        
        try:
            if report_type == "yearly":
                df = ak.stock_financial_report_sina(symbol=symbol, symbol_type="yearly")
            elif report_type == "quarterly":
                df = ak.stock_financial_report_sina(symbol=symbol, symbol_type="quarterly")
            else:
                df = ak.stock_financial_report_sina(symbol=symbol, symbol_type="yearly")
            
            if df.empty:
                return pd.DataFrame()
            
            df = df.rename(columns={
                '报告期': 'end_date',
                '基本每股收益': 'basic_eps',
                '稀释每股收益': 'diluted_eps',
                '营业总收入': 'total_revenue',
                '营业收入': 'operating_revenue',
                '利润总额': 'profit_total',
                '净利润': 'net_profit',
                '总资产': 'total_assets',
                '总负债': 'total_liability',
                '股东权益合计': 'owner_eq'
            })
            
            df['ts_code'] = ts_code
            df['ann_date'] = df['end_date']
            df['f_ann_date'] = df['end_date']
            df['report_type'] = 1 if report_type == "yearly" else 4
            
            df = df[['ts_code', 'ann_date', 'f_ann_date', 'end_date', 'report_type',
                     'basic_eps', 'diluted_eps', 'total_revenue', 'operating_revenue',
                     'profit_total', 'net_profit', 'total_assets', 'total_liability', 'owner_eq']]
            return df
        except Exception as e:
            logger.error(f"Failed to fetch financial report for {ts_code}: {e}")
            return pd.DataFrame()
    
    @retry_with_backoff()
    def fetch_index_daily(self, index_code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        random_delay()
        self._set_random_user_agent()
        
        try:
            df = ak.stock_zh_index_daily(symbol=index_code)
            if df.empty:
                return pd.DataFrame()
            
            df = df.rename(columns={
                '日期': 'trade_date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            })
            
            df['ts_code'] = f"{index_code}.SH" if index_code.startswith("0") else f"{index_code}.SH"
            df['pre_close'] = df['close'].shift(1)
            df['change'] = df['close'] - df['pre_close']
            df['pct_chg'] = (df['change'] / df['pre_close']) * 100
            df['adj_factor'] = 1.0
            
            return df
        except Exception as e:
            logger.error(f"Failed to fetch index daily for {index_code}: {e}")
            return pd.DataFrame()
