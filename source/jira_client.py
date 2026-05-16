import requests
from helpers import with_retries
from constants import REQUEST_TIMEOUT

class JiraClient:
    def __init__(self, base_url: str = "http://localhost:8080", token: str = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    @with_retries
    def get_issue(self, issue_key: str) -> dict:
        """
        Fetch issue metadata.
        Returns the issue dict if found, or None if the issue is a 404.
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the requests Session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

