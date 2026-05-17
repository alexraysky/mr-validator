import pytest
import responses
import socket
import threading
import sys
import os
import json
import importlib
from http.server import HTTPServer
from source.core import Validator
from source.clients import GitLabClient, JiraClient
from source.helpers import TICKET_REGEX, VALID_JIRA_STATES

# Try to import the MockJiraHandler from mocks/mock_jira.py
try:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from mocks.mock_jira import MockJiraHandler
except ImportError:
    MockJiraHandler = None

def is_jira_server_running() -> bool:
    try:
        with socket.create_connection(("localhost", 8080), timeout=1):
            return True
    except OSError:
        return False

# Ensure the mock Jira server is running in a daemon thread if not already running
if MockJiraHandler and not is_jira_server_running():
    server = HTTPServer(("localhost", 8080), MockJiraHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

@pytest.fixture
def gitlab_client():
    return GitLabClient(base_url="https://gitlab.example.com", token="gitlab-token")

@pytest.fixture
def jira_client():
    return JiraClient(base_url="http://localhost:8080", token=None)

@pytest.fixture
def validator(gitlab_client, jira_client):
    return Validator(gitlab_client, jira_client, TICKET_REGEX, VALID_JIRA_STATES)

@responses.activate
def test_integration_valid_jira_state(validator):
    """
    End-to-end validation of the "happy path" where an MR references 
    a valid Jira ticket in an accepted state ("In Review").
    """
    # Enable passthrough to localhost mock Jira server
    responses.add_passthru("http://localhost:8080")
    
    # Mock GitLab MR metadata referencing WMS-1001 (status: In Review - valid)
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/test-proj/merge_requests/1",
        json={
            "draft": False,
            "title": "WMS-1001: Implement authentication",
            "description": "Fixes and hooks",
            "source_branch": "feature/auth"
        },
        status=200
    )
    
    # Mock GitLab commits metadata (no additional tickets)
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/test-proj/merge_requests/1/commits",
        json=[],
        status=200
    )
    
    passed, messages = validator.validate_mr("test-proj", 1)
    
    assert passed is True
    assert any("Rule 1: MR is not in Draft state" in msg for msg in messages)
    assert any("Rule 2: MR references Jira tickets: WMS-1001" in msg for msg in messages)
    assert any("Rule 3: Jira ticket WMS-1001 exists" in msg for msg in messages)
    assert any("Rule 4: Jira ticket WMS-1001 is in valid state 'In Review'" in msg for msg in messages)

@responses.activate
def test_integration_invalid_jira_state(validator):
    """
    E2E test where the referenced Jira ticket is in a rejected state ("In Progress").
    """
    responses.add_passthru("http://localhost:8080")
    
    # Mock GitLab MR metadata referencing WMS-1010 (status: In Progress - invalid)
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/test-proj/merge_requests/2",
        json={
            "draft": False,
            "title": "WMS-1010: Refactor logistics algorithm",
            "description": "Cleanups",
            "source_branch": "feature/picking"
        },
        status=200
    )
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/test-proj/merge_requests/2/commits",
        json=[],
        status=200
    )
    
    passed, messages = validator.validate_mr("test-proj", 2)
    
    assert passed is False
    assert any("Rule 4: Jira ticket WMS-1010 is in invalid state 'In Progress'" in msg for msg in messages)

@responses.activate
def test_integration_missing_jira_ticket(validator):
    """
    E2E test verifying that referencing a non-existent Jira ticket 
    results in a clean failure.
    """
    responses.add_passthru("http://localhost:8080")
    
    # Mock GitLab MR referencing non-existent ticket WMS-9999
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/test-proj/merge_requests/3",
        json={
            "draft": False,
            "title": "WMS-9999: Update reporting pipeline",
            "description": "",
            "source_branch": "feature/reporting"
        },
        status=200
    )
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/test-proj/merge_requests/3/commits",
        json=[],
        status=200
    )
    
    passed, messages = validator.validate_mr("test-proj", 3)
    
    assert passed is False
    assert any("Rule 3: Referenced Jira ticket WMS-9999 doesn't exist" in msg for msg in messages)

@responses.activate
def test_integration_cli_json_end_to_end(mocker, capsys):
    """
    Verifies that running the CLI with `--output json` produces valid, 
    parseable JSON on `stdout` and exits successfully.
    """
    responses.add_passthru("http://localhost:8080")
    
    mr_validator = importlib.import_module("source.mr-validator")
    
    mock_args = mocker.MagicMock()
    mock_args.project_id = "test-proj"
    mock_args.mr_iid = 1
    mock_args.gitlab_url = "https://gitlab.example.com"
    mock_args.jira_url = "http://localhost:8080"
    mock_args.verbose = False
    mock_args.quiet = False
    mock_args.output_format = "json"
    
    mocker.patch.object(mr_validator, 'parse_args', return_value=mock_args)
    mocker.patch.dict(os.environ, {"GITLAB_TOKEN": "", "JIRA_TOKEN": ""})
    
    # Mock GitLab calls
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/test-proj/merge_requests/1",
        json={
            "draft": False,
            "title": "WMS-1001: Implement auth",
            "description": "",
            "source_branch": "auth"
        },
        status=200
    )
    responses.add(
        responses.GET,
        "https://gitlab.example.com/api/v4/projects/test-proj/merge_requests/1/commits",
        json=[],
        status=200
    )
    
    with pytest.raises(SystemExit) as excinfo:
        mr_validator.main()
        
    assert excinfo.value.code == 0
    
    captured = capsys.readouterr()
    # Output should contain a valid, parseable JSON block on stdout
    data = json.loads(captured.out.strip())
    assert data["passed"] is True
    assert data["project_id"] == "test-proj"
    assert data["mr_iid"] == 1
    assert any("WMS-1001 exists" in msg for msg in data["messages"])
