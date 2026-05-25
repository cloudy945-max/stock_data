import time
import logging
import functools
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

def retry_with_backoff(retries=5, delay=1, backoff=2):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries - 1:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff
            return None
        return wrapper
    return decorator

class BaseFetcher:
    def __init__(self):
        self.logger = logger
