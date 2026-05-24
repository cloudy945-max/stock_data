import argparse
import sys
from datetime import datetime
from config import settings
from storage import DuckDBStorage
from tasks import DailyUpdateTask
from utils import setup_logger, get_logger

logger = get_logger(__name__)


def init_database():
    logger.info("Initializing database")
    storage = DuckDBStorage()
    storage.init_tables()
    storage.close()
    logger.info("Database initialized successfully")


def update_stock_list():
    logger.info("Updating stock list")
    task = DailyUpdateTask()
    task.update_stock_basic()
    logger.info("Stock list updated successfully")


def run_daily_update():
    logger.info("Running daily update")
    task = DailyUpdateTask()
    results = task.run_daily_update()
    
    logger.info("Daily update results:")
    for table, stats in results.items():
        logger.info(f"  {table}: {stats['success']} success, {stats['failed']} failed, {stats['no_data']} no data, {stats['total_records']} records")
        if stats['failed_stocks']:
            logger.warning(f"  Failed stocks for {table}: {stats['failed_stocks']}")


def run_history_fetch(start_date: str = "20000101", end_date: str = None):
    logger.info(f"Running history fetch from {start_date} to {end_date or 'now'}")
    task = DailyUpdateTask()
    results = task.run_history_fetch(start_date=start_date, end_date=end_date)
    
    logger.info("History fetch results:")
    for table, stats in results.items():
        logger.info(f"  {table}: {stats['success']} success, {stats['failed']} failed, {stats['total_records']} records")
        if stats['failed_stocks']:
            logger.warning(f"  Failed stocks for {table}: {stats['failed_stocks']}")


def show_stats():
    logger.info("Showing database statistics")
    storage = DuckDBStorage()
    
    tables = ['daily', 'valuation', 'financial', 'stock_basic']
    for table in tables:
        count = storage.get_table_row_count(table)
        logger.info(f"  {table}: {count} records")
    
    dates = storage.get_distinct_dates('daily')
    if dates:
        logger.info(f"  Daily data dates: {len(dates)} dates from {dates[0]} to {dates[-1]}")
    
    stock_count = len(storage.get_stock_list())
    logger.info(f"  Active stocks: {stock_count}")
    
    storage.close()


def main():
    parser = argparse.ArgumentParser(description="A股数据采集与存储系统")
    parser.add_argument('--mode', type=str, required=True, 
                        choices=['init', 'update_stock_list', 'daily', 'history', 'stats'],
                        help='运行模式')
    parser.add_argument('--start_date', type=str, default="20000101",
                        help='历史数据起始日期 (YYYYMMDD)')
    parser.add_argument('--end_date', type=str, default=None,
                        help='历史数据结束日期 (YYYYMMDD)')
    
    args = parser.parse_args()
    
    setup_logger()
    
    start_time = datetime.now()
    logger.info(f"Started at {start_time}")
    
    try:
        if args.mode == 'init':
            init_database()
        
        elif args.mode == 'update_stock_list':
            update_stock_list()
        
        elif args.mode == 'daily':
            run_daily_update()
        
        elif args.mode == 'history':
            run_history_fetch(start_date=args.start_date, end_date=args.end_date)
        
        elif args.mode == 'stats':
            show_stats()
        
        else:
            logger.error(f"Unknown mode: {args.mode}")
            sys.exit(1)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Completed at {end_time}, duration: {duration:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
