import pytest
from source.validator import Validator
from source.gitlab_client import GitLabClient
from source.jira_client import JiraClient
from source.constants import TICKET_REGEX, VALID_JIRA_STATES
from unittest.mock import MagicMock

@pytest.fixture
def validator():
    mock_gitlab = MagicMock(spec=GitLabClient)
    mock_jira = MagicMock(spec=JiraClient)
    return Validator(mock_gitlab, mock_jira, TICKET_REGEX, VALID_JIRA_STATES)

def test_extract_tickets(validator):
    mr_data = {
        'title': 'WMS-1234: Add new feature',
        'description': 'This fixes WMS-5678 and also WMS-1234.',
        'source_branch': 'feature/WMS-9999-new-stuff'
    }
    commits = [
        {'title': 'WMS-0001 fix', 'message': 'Fixing WMS-0001 details'},
        {'title': 'no ticket here', 'message': 'just a typo fix'}
    ]
    
    tickets = validator.extract_tickets(mr_data, commits)
    
    assert tickets == {'WMS-1234', 'WMS-5678', 'WMS-9999', 'WMS-0001'}

def test_extract_tickets_empty(validator):
    mr_data = {'title': 'No ticket here'}
    commits = []
    assert validator.extract_tickets(mr_data, commits) == set()

def test_rule1_draft_mr(validator):
    validator.gitlab.get_merge_request.return_value = {'draft': True, 'title': 'WMS-123'}
    validator.gitlab.get_merge_request_commits.return_value = []
    
    passed, messages = validator.validate_mr('proj', 1)
    
    assert not passed
    assert any("Rule 1: MR is in Draft state" in msg for msg in messages)

def test_rule2_zero_tickets(validator):
    validator.gitlab.get_merge_request.return_value = {'draft': False, 'title': 'No tickets here'}
    validator.gitlab.get_merge_request_commits.return_value = []
    
    passed, messages = validator.validate_mr('proj', 1)
    
    assert not passed
    assert any("Rule 2: MR references zero Jira tickets" in msg for msg in messages)

def test_rule3_missing_ticket(validator):
    validator.gitlab.get_merge_request.return_value = {'draft': False, 'title': 'WMS-404'}
    validator.gitlab.get_merge_request_commits.return_value = []
    
    # Jira returns None for 404
    validator.jira.get_issue.return_value = None
    
    passed, messages = validator.validate_mr('proj', 1)
    
    assert not passed
    assert any("Rule 3: Referenced Jira ticket WMS-404 doesn't exist" in msg for msg in messages)

def test_rule4_invalid_status(validator):
    validator.gitlab.get_merge_request.return_value = {'draft': False, 'title': 'WMS-100'}
    validator.gitlab.get_merge_request_commits.return_value = []
    
    validator.jira.get_issue.return_value = {
        'fields': {
            'status': {'name': 'In Progress'}
        }
    }
    
    passed, messages = validator.validate_mr('proj', 1)
    
    assert not passed
    assert any("Rule 4: Jira ticket WMS-100 is in invalid state" in msg for msg in messages)

def test_all_rules_pass(validator):
    validator.gitlab.get_merge_request.return_value = {'draft': False, 'title': 'WMS-200'}
    validator.gitlab.get_merge_request_commits.return_value = []
    
    validator.jira.get_issue.return_value = {
        'fields': {
            'status': {'name': 'In Review'}
        }
    }
    
    passed, messages = validator.validate_mr('proj', 1)
    
    assert passed
    assert any("Rule 1: MR is not in Draft state" in msg for msg in messages)
    assert any("Rule 2: MR references Jira tickets: WMS-200" in msg for msg in messages)
    assert any("Rule 3: Jira ticket WMS-200 exists" in msg for msg in messages)
    assert any("Rule 4: Jira ticket WMS-200 is in valid state 'In Review'" in msg for msg in messages)

def test_strip_code_blocks(validator):
    # Test multi-line blocks
    text_with_block = "Keep this. ```\nIgnore this WMS-123\n``` And this."
    assert validator._strip_code_blocks(text_with_block).strip() == "Keep this.  And this."
    
    # Test inline blocks
    text_with_inline = "Keep WMS-456. `Ignore WMS-789` Keep."
    assert validator._strip_code_blocks(text_with_inline) == "Keep WMS-456.  Keep."
    
    # Test nested/mixed
    text_mixed = "WMS-1. `WMS-2` ```WMS-3``` WMS-4"
    assert validator._strip_code_blocks(text_mixed).strip() == "WMS-1.   WMS-4"

    # Test empty/None
    assert validator._strip_code_blocks("") == ""
    assert validator._strip_code_blocks(None) == ""

def test_extract_tickets_ignoring_code_blocks(validator):
    mr_data = {
        'title': 'WMS-101: Fix bug',
        'description': 'Check this code: `WMS-102` and ```WMS-103```. Also see WMS-104.',
        'source_branch': 'WMS-105-branch'
    }
    commits = []
    
    tickets = validator.extract_tickets(mr_data, commits)
    
    # WMS-101, WMS-104, WMS-105 should be found
    # WMS-102, WMS-103 should be ignored
    assert tickets == {'WMS-101', 'WMS-104', 'WMS-105'}
