from helpers import with_retries, REQUEST_TIMEOUT
from clients.base_client import BaseClient

class JiraClient(BaseClient):
    def __init__(self, base_url: str = "http://localhost:8080", token: str = None):
        super().__init__(base_url)
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    @property
    def auth_endpoint(self) -> str:
        return "/rest/api/3/myself"


    @with_retries
    def get_issue(self, issue_key: str) -> dict:
        """
        Fetch issue metadata.
        Returns the issue dict if found, or None if the issue is a 404.
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        params = {"fields": "status,issuetype"}
        response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
