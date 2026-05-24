import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict
from config import settings
from storage import DuckDBStorage
from utils import get_logger

logger = get_logger(__name__)


class Monitor:
    def __init__(self):
        self.storage = DuckDBStorage()
    
    def get_missing_data_report(self) -> Dict[str, list]:
        report = {
            'missing_daily': [],
            'missing_valuation': [],
            'missing_financial': [],
            'stale_stocks': []
        }
        
        stock_list = self.storage.get_stock_list()
        
        for ts_code in stock_list:
            daily_date = self.storage.get_latest_date('daily', ts_code)
            val_date = self.storage.get_latest_date('valuation', ts_code)
            fin_date = self.storage.get_latest_financial_date(ts_code)
            
            if not daily_date:
                report['missing_daily'].append(ts_code)
            
            if not val_date:
                report['missing_valuation'].append(ts_code)
            
            if not fin_date:
                report['missing_financial'].append(ts_code)
        
        return report
    
    def get_database_stats(self) -> Dict[str, int]:
        stats = {}
        tables = ['daily', 'valuation', 'financial', 'stock_basic']
        
        for table in tables:
            stats[table] = self.storage.get_table_row_count(table)
        
        stats['active_stocks'] = len(self.storage.get_stock_list())
        return stats
    
    def generate_summary(self, run_results: Dict = None) -> str:
        stats = self.get_database_stats()
        missing = self.get_missing_data_report()
        
        summary = f"""
A股数据采集系统运行报告
========================

运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

数据库统计:
-----------
- 股票列表: {stats['active_stocks']} 只
- 日线数据: {stats['daily']} 条记录
- 估值数据: {stats['valuation']} 条记录
- 财务数据: {stats['financial']} 条记录

缺失数据统计:
-------------
- 缺失日线数据: {len(missing['missing_daily'])} 只股票
- 缺失估值数据: {len(missing['missing_valuation'])} 只股票
- 缺失财务数据: {len(missing['missing_financial'])} 只股票
"""
        
        if run_results:
            summary += "\n本次更新结果:\n-------------\n"
            for table, results in run_results.items():
                summary += f"- {table}: {results['success']}成功, {results['failed']}失败, {results['total_records']}条记录\n"
                if results['failed_stocks']:
                    summary += f"  失败股票: {', '.join(results['failed_stocks'][:10])}{'...' if len(results['failed_stocks']) > 10 else ''}\n"
        
        return summary.strip()
    
    def send_email(self, subject: str, content: str):
        if not settings.MAIL_ENABLED:
            logger.info("Email notification is disabled")
            return
        
        if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
            logger.error("Email credentials not configured")
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.MAIL_USERNAME
            msg['To'] = ', '.join(settings.MAIL_RECEIVERS)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            with smtplib.SMTP_SSL(settings.MAIL_SMTP_SERVER, settings.MAIL_SMTP_PORT) as server:
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                server.send_message(msg)
            
            logger.info("Email notification sent successfully")
        
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
    
    def run_monitor(self, run_results: Dict = None):
        summary = self.generate_summary(run_results)
        logger.info(f"\n{summary}")
        
        if settings.MAIL_ENABLED:
            subject = f"A股数据采集系统 - {datetime.now().strftime('%Y-%m-%d')}"
            self.send_email(subject, summary)
        
        self.storage.close()
        return summary


def main():
    monitor = Monitor()
    monitor.run_monitor()


if __name__ == "__main__":
    main()
