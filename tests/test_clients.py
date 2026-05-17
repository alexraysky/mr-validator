import pytest
import responses
import requests
from source.clients import GitLabClient, JiraClient
from source.helpers import REQUEST_TIMEOUT

@responses.activate
def test_gitlab_client_headers_and_encoding():
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

def test_gitlab_client_timeout_setting(mocker):
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
    client = JiraClient()
    mock_get = mocker.patch.object(client.session, 'get')
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {}
    
    client.get_issue("WMS-1")
    
    _, kwargs = mock_get.call_args
    assert kwargs['timeout'] == REQUEST_TIMEOUT
