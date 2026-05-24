import argparse
import sys
from datetime import datetime
from config import settings
from storage import DuckDBStorage
from tasks import DailyUpdateTask
from utils import setup_logger, get_logger

logger = get_logger(__name__)


def init_database():
    storage = None
    try:
        logger.info("Initializing database...")
        storage = DuckDBStorage()
        storage.init_tables()
        logger.info("Database tables created successfully")
        
        logger.info("Running VACUUM to optimize database...")
        storage.vacuum()
        logger.info("VACUUM completed")
        
        logger.info("Running ANALYZE to update statistics...")
        storage.analyze()
        logger.info("ANALYZE completed")
        
        logger.info("Database initialized successfully")
    finally:
        if storage:
            storage.close()


def update_stock_list():
    task = None
    try:
        logger.info("Updating stock list...")
        task = DailyUpdateTask()
        count = task.update_stock_basic()
        logger.info(f"Stock list updated: {count} records")
    finally:
        if task:
            task.storage.close()


def run_daily_update():
    task = None
    try:
        logger.info("=" * 60)
        logger.info("Starting daily update")
        logger.info("=" * 60)
        
        task = DailyUpdateTask()
        results = task.run_daily_update()
        
        logger.info("=" * 60)
        logger.info("Daily update results:")
        for table, stats in results.items():
            logger.info(f"  [{table.upper()}] Success: {stats['success']}, Failed: {stats['failed']}, "
                       f"NoData: {stats['no_data']}, Records: {stats['total_records']}")
            if stats['failed_stocks']:
                failed_preview = stats['failed_stocks'][:5]
                logger.warning(f"  Failed stocks: {failed_preview}..."
                             if len(stats['failed_stocks']) > 5 else f"  Failed stocks: {failed_preview}")
        logger.info("=" * 60)
    finally:
        if task:
            task.storage.close()


def run_history_fetch(start_date: str = "20000101", end_date: str = None):
    task = None
    try:
        logger.info("=" * 60)
        logger.info(f"History fetch: {start_date} to {end_date or 'now'}")
        logger.info("=" * 60)
        
        task = DailyUpdateTask()
        results = task.run_history_fetch(start_date=start_date, end_date=end_date)
        
        logger.info("=" * 60)
        logger.info("History fetch results:")
        for table, stats in results.items():
            logger.info(f"  [{table.upper()}] Success: {stats['success']}, Failed: {stats['failed']}, "
                       f"Records: {stats['total_records']}")
            if stats['failed_stocks']:
                failed_preview = stats['failed_stocks'][:5]
                logger.warning(f"  Failed stocks: {failed_preview}..."
                             if len(stats['failed_stocks']) > 5 else f"  Failed stocks: {failed_preview}")
        logger.info("=" * 60)
    finally:
        if task:
            task.storage.close()


def show_stats():
    storage = None
    try:
        logger.info("=" * 60)
        logger.info("Database Statistics")
        logger.info("=" * 60)
        
        storage = DuckDBStorage()
        
        tables = ['daily', 'valuation', 'financial', 'stock_basic']
        for table in tables:
            count = storage.get_table_row_count(table)
            logger.info(f"  [{table.upper()}] {count:,} records")
        
        dates = storage.get_distinct_dates('daily')
        if dates:
            logger.info(f"  [DAILY DATE RANGE] {len(dates)} trading days from {dates[0]} to {dates[-1]}")
        
        stock_count = len(storage.get_stock_list())
        logger.info(f"  [ACTIVE STOCKS] {stock_count:,} stocks")
        
        if getattr(settings, 'PYTHONARM_MODE', False):
            logger.info(f"  [ARM MODE] Enabled - concurrency: {settings.MAX_CONCURRENT}, "
                       f"DuckDB threads: {settings.DUCKDB_THREADS}, "
                       f"Memory limit: {settings.DB_MEMORY_LIMIT}")
        
        logger.info("=" * 60)
    finally:
        if storage:
            storage.close()


def main():
    parser = argparse.ArgumentParser(
        description="A股数据采集与存储系统 - ARM NAS 优化版",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ARM NAS 部署注意事项:
  - 本系统已针对 ARM64/aarch64 架构优化
  - 默认并发数: 2 (降低 CPU 占用)
  - 请求间隔: 2.5-6秒 (避免过热)
  - DuckDB 内存限制: 2GB (防止内存耗尽)

Examples:
  python main.py --mode init                    # Initialize database
  python main.py --mode update_stock_list       # Update stock list
  python main.py --mode daily                   # Daily update
  python main.py --mode history --start 20200101 --end 20201231
  python main.py --mode stats                   # Show database statistics

Cron 配置 (推荐在 CPU 空闲时段运行):
  30 18 * * * cd /path/to/stock_data && python main.py --mode daily >> logs/cron.log 2>&1
        """
    )
    parser.add_argument('--mode', type=str, required=True,
                        choices=['init', 'update_stock_list', 'daily', 'history', 'stats'],
                        help='运行模式: init=初始化数据库, update_stock_list=更新股票列表, '
                             'daily=每日更新, history=历史数据拉取, stats=显示统计')
    parser.add_argument('--start', type=str, default="20000101",
                        help='历史数据起始日期 (YYYYMMDD)')
    parser.add_argument('--end', type=str, default=None,
                        help='历史数据结束日期 (YYYYMMDD)')
    
    args = parser.parse_args()
    
    setup_logger()
    
    start_time = datetime.now()
    
    arm_mode = getattr(settings, 'PYTHONARM_MODE', False)
    
    logger.info(f"{'=' * 60}")
    logger.info(f"Stock Data System Started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Mode: {args.mode}")
    if arm_mode:
        logger.info(f"[ARM MODE] Running on ARM NAS - concurrency limited to {settings.MAX_CONCURRENT}")
        logger.info(f"[ARM MODE] DuckDB threads: {settings.DUCKDB_THREADS}, Memory limit: {settings.DB_MEMORY_LIMIT}")
    logger.info(f"{'=' * 60}")
    
    try:
        if args.mode == 'init':
            init_database()
        elif args.mode == 'update_stock_list':
            update_stock_list()
        elif args.mode == 'daily':
            run_daily_update()
        elif args.mode == 'history':
            run_history_fetch(start_date=args.start, end_date=args.end)
        elif args.mode == 'stats':
            show_stats()
        else:
            logger.error(f"Unknown mode: {args.mode}")
            sys.exit(1)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"{'=' * 60}")
        logger.info(f"Completed at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        
        if arm_mode:
            logger.info(f"[ARM MODE] Task completed successfully - system running in low-power mode")
        
        logger.info(f"{'=' * 60}")
        
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
