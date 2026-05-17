import pytest
import responses
import requests
from source.clients import GitLabClient, JiraClient
from source.helpers import REQUEST_TIMEOUT

@responses.activate
def test_gitlab_client_headers_and_encoding():
    """
    Verifies that GitLabClient sets the required 
    `Private-Token` header and correctly URL-encodes project IDs.
    """
    client = GitLabClient(token="secret-token")
    project_id = "group/project"
    mr_iid = 123
    
    # Notice the %2F for group/project
    url = f"https://gitlab.com/api/v4/projects/group%2Fproject/merge_requests/{mr_iid}"
    
    responses.add(
        responses.GET,
        url,
        json={"id": 1},
        status=200
    )
    
    client.get_merge_request(project_id, mr_iid)
    
    assert responses.calls[0].request.headers["Private-Token"] == "secret-token"

@responses.activate
def test_jira_client_404_returns_none():
    """
    Checks that JiraClient gracefully returns `None` 
    when it encounters a 404 response (non-existent ticket).
    """
    client = JiraClient()
    url = "http://localhost:8080/rest/api/3/issue/WMS-404"
    
    responses.add(
        responses.GET,
        url,
        status=404
    )
    
    result = client.get_issue("WMS-404")
    assert result is None

@responses.activate
def test_jira_client_auth_header():
    """
    Verifies that JiraClient properly formats and sets
    the `Authorization` header with `Bearer <token>`.
    """
    client = JiraClient(token="jira-token")
    url = "http://localhost:8080/rest/api/3/issue/WMS-1"
    
    responses.add(
        responses.GET,
        url,
        json={"id": "WMS-1"},
        status=200
    )
    
    client.get_issue("WMS-1")
    assert responses.calls[0].request.headers["Authorization"] == "Bearer jira-token"

@responses.activate
def test_jira_client_verify_auth():
    """
    Verifies that JiraClient.verify_auth returns True on 200, False on 401/403.
    """
    client = JiraClient()
    url = "http://localhost:8080/rest/api/3/myself"
    
    responses.add(responses.GET, url, status=200)
    assert client.verify_auth() is True

    responses.replace(responses.GET, url, status=401)
    assert client.verify_auth() is False

    responses.replace(responses.GET, url, status=403)
    assert client.verify_auth() is False

def test_gitlab_client_timeout_setting(mocker):
    """
    Ensures GitLabClient enforces a `REQUEST_TIMEOUT` 
    when making HTTP requests to prevent indefinite hanging.
    """
    # Use pytest-mock (mocker) to verify the timeout arg is passed
    client = GitLabClient()
    # We patch the underlying session.get
    mock_get = mocker.patch.object(client.session, 'get')
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {}
    
    client.get_merge_request("p", 1)
    
    _, kwargs = mock_get.call_args
    assert kwargs['timeout'] == REQUEST_TIMEOUT

def test_jira_client_timeout_setting(mocker):
    """
    Ensures JiraClient enforces a `REQUEST_TIMEOUT` 
    when making HTTP requests.
    """
    client = JiraClient()
    mock_get = mocker.patch.object(client.session, 'get')
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {}
    
    client.get_issue("WMS-1")
    
    _, kwargs = mock_get.call_args
    assert kwargs['timeout'] == REQUEST_TIMEOUT
