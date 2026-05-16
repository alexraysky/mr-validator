import time
from functools import wraps
from constants import MAX_RETRIES, RETRY_BACKOFF_BASE

def print_red(message):
    print(f"\033[91m{message}\033[0m")

def print_green(message):
    print(f"\033[92m{message}\033[0m")

def print_yellow(message):
    print(f"\033[93m{message}\033[0m")

def print_blue(message):
    print(f"\033[94m{message}\033[0m")

def print_purple(message):
    print(f"\033[95m{message}\033[0m")

def print_cyan(message):
    print(f"\033[96m{message}\033[0m")

def print_white(message):
    print(f"\033[97m{message}\033[0m")

def with_retries(func):
    """
    Decorator to wrap a function with retry logic.
    Retries up to MAX_RETRIES times with exponential backoff.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        last_exception = None
        for i in range(MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if i == MAX_RETRIES:
                    break
                wait_time = pow(RETRY_BACKOFF_BASE, i + 1)
                print_yellow(f"Request failed: {e}. Retrying in {wait_time}s... (Retry {i+1}/{MAX_RETRIES})")
                time.sleep(wait_time)
        raise last_exception
    return wrapper