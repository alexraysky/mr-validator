import time
import requests
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
    Retries only on network-related exceptions (ConnectionError, Timeout) and HTTP 5xx or 429.
    Implements special handling for HTTP 429 to respect the Retry-After header.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        last_exception = None
        for i in range(MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.HTTPError as e:
                last_exception = e
                status_code = e.response.status_code if e.response is not None else None

                if status_code == 429:
                    if i == MAX_RETRIES:
                        break
                    
                    retry_after = None
                    if e.response is not None and e.response.headers:
                        retry_after_val = e.response.headers.get("Retry-After")
                        if retry_after_val:
                            try:
                                retry_after = int(retry_after_val)
                            except ValueError:
                                pass
                    
                    wait_time = retry_after if retry_after is not None else pow(RETRY_BACKOFF_BASE, i + 1)
                    print_yellow(f"Rate limited (429). Retrying in {wait_time}s... (Retry {i+1}/{MAX_RETRIES})")
                    time.sleep(wait_time)
                elif status_code is not None and status_code >= 500:
                    if i == MAX_RETRIES:
                        break
                    wait_time = pow(RETRY_BACKOFF_BASE, i + 1)
                    print_yellow(f"Server error ({status_code}). Retrying in {wait_time}s... (Retry {i+1}/{MAX_RETRIES})")
                    time.sleep(wait_time)
                else:
                    # Client errors (400, 401, 403, 404, etc.) are raised immediately
                    raise
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                last_exception = e
                if i == MAX_RETRIES:
                    break
                wait_time = pow(RETRY_BACKOFF_BASE, i + 1)
                print_yellow(f"Network error ({e.__class__.__name__}): {e}. Retrying in {wait_time}s... (Retry {i+1}/{MAX_RETRIES})")
                time.sleep(wait_time)
            except Exception:
                # Any other programming error or unexpected exception is raised immediately
                raise
        raise last_exception
    return wrapper
