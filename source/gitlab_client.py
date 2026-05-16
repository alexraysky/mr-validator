import urllib.parse
import requests
from helpers import with_retries

class GitLabClient:
    def __init__(self, base_url: str = "https://gitlab.com", token: str = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Private-Token": token})

    @with_retries
    def get_merge_request(self, project_id: str, mr_iid: int) -> dict:
        """Fetch MR metadata like title, description, state, draft status, and source branch."""
        project_encoded = urllib.parse.quote(project_id, safe='')
        url = f"{self.base_url}/api/v4/projects/{project_encoded}/merge_requests/{mr_iid}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    @with_retries
    def get_merge_request_commits(self, project_id: str, mr_iid: int) -> list:
        """Fetch commits associated with the MR."""
        project_encoded = urllib.parse.quote(project_id, safe='')
        url = f"{self.base_url}/api/v4/projects/{project_encoded}/merge_requests/{mr_iid}/commits"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
