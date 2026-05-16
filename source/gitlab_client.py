import urllib.parse
import requests
from helpers import with_retries
from constants import REQUEST_TIMEOUT

class GitLabClient:
    def __init__(self, base_url: str = "https://gitlab.com", token: str = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Private-Token": token})

    def verify_auth(self) -> bool:
        """
        Lightweight check to verify that the token is valid.
        Returns True if authenticated successfully, False if unauthorized,
        or raises a requests exception on network failures.
        """
        url = f"{self.base_url}/api/v4/user"
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


    @with_retries
    def get_merge_request(self, project_id: str, mr_iid: int) -> dict:
        """Fetch MR metadata like title, description, state, draft status, and source branch."""
        project_encoded = urllib.parse.quote(project_id, safe='')
        url = f"{self.base_url}/api/v4/projects/{project_encoded}/merge_requests/{mr_iid}"
        response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()

    @with_retries
    def get_merge_request_commits(self, project_id: str, mr_iid: int) -> list:
        """Fetch commits associated with the MR."""
        project_encoded = urllib.parse.quote(project_id, safe='')
        url = f"{self.base_url}/api/v4/projects/{project_encoded}/merge_requests/{mr_iid}/commits"
        response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the requests Session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

