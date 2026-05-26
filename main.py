import logging
import sys
from config import settings
from tasks import DailyUpdateTask
from storage import DuckDBStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def init_db():
    storage = DuckDBStorage()
    storage.close()

def update_stock_list():
    task = DailyUpdateTask()
    task.update_stock_basic()
    task.close()

def run_daily_update():
    task = DailyUpdateTask()
    
    # 关键修复：从数据库读取股票
    storage = DuckDBStorage()
    stocks = storage.conn.execute("SELECT ts_code FROM stock_basic").fetchall()
    stock_list = [s[0] for s in stocks]
    storage.close()
    
    logger.info(f"Total stocks to update: {len(stock_list)}")
    
    if not stock_list:
        logger.warning("No stocks to update")
        return
    
    task.run_daily_update()
    task.close()

def show_help():
    print("Usage: python main.py --mode [init|update_stock_list|daily|help]")

def main():
    init_db()
    if len(sys.argv) < 3 or sys.argv[1] != "--mode":
        show_help()
        return

    mode = sys.argv[2]
    try:
        if mode == "init":
            logger.info("Database initialized")
        elif mode == "update_stock_list":
            update_stock_list()
        elif mode == "daily":
            run_daily_update()
        elif mode == "help":
            show_help()
        else:
            logger.error(f"Unknown mode: {mode}")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    main()
