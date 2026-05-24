import pandas as pd
import akshare as ak
import random
from typing import Optional
from config import settings, USER_AGENT_POOL
from utils import get_logger, random_delay, retry_with_backoff, normalize_ts_code

logger = get_logger(__name__)


class AKShareFetcher:
    def __init__(self):
        self._data_source = "AKShare"
        self._setup_html5lib()
        self._setup_session()
    
    def _setup_html5lib(self):
        try:
            ak.set_option('BeautifulSoup', {'features': 'html5lib'})
            logger.info("[AKShare] Using html5lib parser for BeautifulSoup")
        except Exception as e:
            logger.warning(f"[AKShare] Failed to set html5lib parser: {e}, will use default parser")
    
    def _setup_session(self):
        if settings.PROXY_ENABLED and settings.PROXY_URL:
            ak.set_proxy(settings.PROXY_URL)
    
    def _set_random_user_agent(self):
        ak.headers = {"User-Agent": random.choice(USER_AGENT_POOL)}
    
    def _ensure_html5lib(self):
        try:
            ak.set_option('BeautifulSoup', {'features': 'html5lib'})
        except Exception:
            pass
    
    @retry_with_backoff()
    def fetch_stock_basic(self) -> pd.DataFrame:
        random_delay()
        self._set_random_user_agent()
        self._ensure_html5lib()
        
        try:
            df = ak.stock_zh_a_spot()
            if df.empty:
                logger.warning("[AKShare] stock_zh_a_spot returned empty")
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
            
            logger.info(f"[AKShare] Fetched {len(df)} stocks from stock_zh_a_spot (using html5lib parser)")
            return df[['ts_code', 'symbol', 'name', 'area', 'industry', 'list_date', 'status']]
        except Exception as e:
            logger.error(f"[AKShare] Failed to fetch stock_basic (using html5lib parser): {e}")
            return pd.DataFrame()
    
    @retry_with_backoff()
    def fetch_daily(self, ts_code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        ts_code = normalize_ts_code(ts_code)
        if not ts_code:
            logger.warning(f"[AKShare] Invalid ts_code: {ts_code}")
            return pd.DataFrame()
        
        symbol = ts_code.split('.')[0]
        random_delay()
        self._set_random_user_agent()
        self._ensure_html5lib()
        
        try:
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
            if df.empty:
                logger.debug(f"[AKShare] No daily data for {ts_code}")
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
            
            logger.debug(f"[AKShare] Got {len(df)} daily records for {ts_code} (using html5lib parser)")
            return df
        except Exception as e:
            logger.error(f"[AKShare] Failed to fetch daily data for {ts_code} (using html5lib parser): {e}")
            return pd.DataFrame()
    
    @retry_with_backoff()
    def fetch_valuation(self, ts_code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        ts_code = normalize_ts_code(ts_code)
        if not ts_code:
            logger.warning(f"[AKShare] Invalid ts_code for valuation: {ts_code}")
            return pd.DataFrame()
        
        symbol = ts_code.split('.')[0]
        random_delay()
        self._set_random_user_agent()
        self._ensure_html5lib()
        
        try:
            df = ak.stock_a_indicator_lg(symbol=symbol)
            if df.empty:
                logger.warning(f"[AKShare] No valuation data for {ts_code}")
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
            
            date_range_years = 0
            if start_date and end_date:
                from datetime import datetime
                try:
                    start = datetime.strptime(start_date, "%Y-%m-%d")
                    end = datetime.strptime(end_date, "%Y-%m-%d")
                    date_range_years = (end - start).days / 365.25
                except:
                    pass
            
            if date_range_years > 1 and len(df) < 100:
                logger.warning(
                    f"[AKShare] Valuation data for {ts_code} may be incomplete. "
                    f"Expected ~{int(date_range_years * 250)} records for {date_range_years:.1f} years, got {len(df)}. "
                    f"Consider using alternative sources for historical valuation data."
                )
            
            df = df[['ts_code', 'trade_date', 'pe', 'pe_ttm', 'pb', 'ps', 
                     'ps_ttm', 'dv_ratio', 'dv_ttm', 'total_mv', 'circ_mv']]
            
            logger.debug(f"[AKShare] Got {len(df)} valuation records for {ts_code} (using html5lib parser)")
            return df
        except Exception as e:
            logger.error(f"[AKShare] Failed to fetch valuation for {ts_code} (using html5lib parser): {e}")
            return pd.DataFrame()
    
    @retry_with_backoff()
    def fetch_financial_report(self, ts_code: str, report_type: str = "yearly") -> pd.DataFrame:
        ts_code = normalize_ts_code(ts_code)
        if not ts_code:
            logger.warning(f"[AKShare] Invalid ts_code for financial: {ts_code}")
            return pd.DataFrame()
        
        symbol = ts_code.split('.')[0]
        random_delay()
        self._set_random_user_agent()
        self._ensure_html5lib()
        
        try:
            if report_type == "yearly":
                df = ak.stock_financial_report_sina(symbol=symbol, symbol_type="yearly")
            elif report_type == "quarterly":
                df = ak.stock_financial_report_sina(symbol=symbol, symbol_type="quarterly")
            else:
                df = ak.stock_financial_report_sina(symbol=symbol, symbol_type="yearly")
            
            if df.empty:
                logger.warning(f"[AKShare] No {report_type} financial data for {ts_code}")
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
            
            logger.debug(f"[AKShare] Got {len(df)} {report_type} financial records for {ts_code} (using html5lib parser)")
            return df
        except Exception as e:
            logger.error(f"[AKShare] Failed to fetch financial report for {ts_code} (using html5lib parser): {e}")
            return pd.DataFrame()
    
    @retry_with_backoff()
    def fetch_index_daily(self, index_code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        random_delay()
        self._set_random_user_agent()
        self._ensure_html5lib()
        
        try:
            df = ak.stock_zh_index_daily(symbol=index_code)
            if df.empty:
                logger.warning(f"[AKShare] No index data for {index_code}")
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
            
            logger.debug(f"[AKShare] Got {len(df)} index records for {index_code} (using html5lib parser)")
            return df
        except Exception as e:
            logger.error(f"[AKShare] Failed to fetch index daily for {index_code} (using html5lib parser): {e}")
            return pd.DataFrame()
