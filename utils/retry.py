import time
import random
from functools import wraps
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config import settings


def random_delay(min_delay: float = None, max_delay: float = None):
    min_delay = min_delay or settings.REQUEST_DELAY_MIN
    max_delay = max_delay or settings.REQUEST_DELAY_MAX
    time.sleep(random.uniform(min_delay, max_delay))


def retry_with_backoff(max_retries: int = None):
    max_retries = max_retries or settings.MAX_RETRIES
    
    def decorator(func):
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(Exception)
        )
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def retry_with_long_delay(max_retries: int = None):
    """增强版重试装饰器，适合 ARM NAS 网络不稳定环境
    - 每次重试间隔 3-8 秒随机延时
    - 最多重试 5 次
    """
    max_retries = max_retries or 5
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    wait_time = random.uniform(3, 8)
                    time.sleep(wait_time)
                    if attempt < max_retries - 1:
                        pass
            
            raise last_exception
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = None):
    max_retries = max_retries or settings.MAX_RETRIES
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    wait_time = (2 ** attempt) + random.random()
                    time.sleep(wait_time)
            
            raise last_exception
        return wrapper
    return decorator
