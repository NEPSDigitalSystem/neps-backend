import time
import random
from functools import wraps
from typing import Callable, TypeVar

T = TypeVar('T')

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """Retry decorator with exponential backoff for NEPS services"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = base_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        raise
                    
                    # Jitter: add randomness to prevent thundering herd
                    jitter = random.uniform(0, delay * 0.1)
                    sleep_time = min(delay + jitter, max_delay)
                    
                    time.sleep(sleep_time)
                    delay *= 2  # Exponential backoff
            
            return None  # Unreachable
        return wrapper
    return decorator
