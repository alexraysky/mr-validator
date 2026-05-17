import requests
from abc import ABC, abstractmethod
from helpers import REQUEST_TIMEOUT

class BaseClient(ABC):
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    @property
    @abstractmethod
    def auth_endpoint(self) -> str:
        """Return the endpoint used for verifying authentication."""
        pass

    def verify_auth(self) -> bool:
        """
        Lightweight check to verify that the token is valid.
        Returns True if authenticated successfully, False if unauthorized,
        or raises a requests exception on network failures.
        """
        url = f"{self.base_url}{self.auth_endpoint}"
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return True
            if response.status_code in (401, 403):
                return False
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code in (401, 403):
                return False
            raise
        return False

    def close(self):
        """Close the requests Session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
