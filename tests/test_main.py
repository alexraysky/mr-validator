import pytest
import sys
import importlib
import requests

@pytest.fixture
def mr_validator():
    # Dynamically import due to hyphen in module name
    return importlib.import_module("source.mr-validator")

def test_main_exit_success(mocker, mr_validator):
    mock_args = mocker.MagicMock()
    mock_args.project_id = "proj"
    mock_args.mr_iid = 1
    mock_args.gitlab_url = "http://gitlab"
    mock_args.jira_url = "http://jira"
    mock_args.output_format = "text"
    
    mocker.patch.object(mr_validator, 'parse_args', return_value=mock_args)
    mocker.patch.object(mr_validator, 'setup_logging')
    
    # Mock environment token to trigger verify_auth path
    mocker.patch('os.getenv', side_effect=lambda name, default=None: "mocked-token" if "TOKEN" in name else default)
    
    mock_gitlab = mocker.MagicMock()
    mock_gitlab.verify_auth.return_value = True
    mocker.patch.object(mr_validator, 'GitLabClient', return_value=mock_gitlab)
    mocker.patch.object(mr_validator, 'JiraClient')
    
    mock_validator_instance = mocker.MagicMock()
    mock_validator_instance.validate_mr.return_value = (True, ["[PASS] Rule 1"])
    mocker.patch.object(mr_validator, 'Validator', return_value=mock_validator_instance)
    
    with pytest.raises(SystemExit) as excinfo:
        mr_validator.main()
    assert excinfo.value.code == 0

def test_main_exit_validation_failure(mocker, mr_validator):
    mock_args = mocker.MagicMock()
    mock_args.project_id = "proj"
    mock_args.mr_iid = 1
    mock_args.gitlab_url = "http://gitlab"
    mock_args.jira_url = "http://jira"
    mock_args.output_format = "text"
    
    mocker.patch.object(mr_validator, 'parse_args', return_value=mock_args)
    mocker.patch.object(mr_validator, 'setup_logging')
    mocker.patch('os.getenv', return_value=None)  # No token
    
    mocker.patch.object(mr_validator, 'GitLabClient')
    mocker.patch.object(mr_validator, 'JiraClient')
    
    mock_validator_instance = mocker.MagicMock()
    mock_validator_instance.validate_mr.return_value = (False, ["[FAIL] Rule 1"])
    mocker.patch.object(mr_validator, 'Validator', return_value=mock_validator_instance)
    
    with pytest.raises(SystemExit) as excinfo:
        mr_validator.main()
    assert excinfo.value.code == 1

def test_main_exit_invalid_token(mocker, mr_validator):
    mock_args = mocker.MagicMock()
    mock_args.project_id = "proj"
    mock_args.mr_iid = 1
    mock_args.gitlab_url = "http://gitlab"
    mock_args.jira_url = "http://jira"
    
    mocker.patch.object(mr_validator, 'parse_args', return_value=mock_args)
    mocker.patch.object(mr_validator, 'setup_logging')
    mocker.patch('os.getenv', side_effect=lambda name, default=None: "bad-token" if "TOKEN" in name else default)
    
    mock_gitlab = mocker.MagicMock()
    mock_gitlab.verify_auth.return_value = False  # Token validation failure!
    mocker.patch.object(mr_validator, 'GitLabClient', return_value=mock_gitlab)
    
    with pytest.raises(SystemExit) as excinfo:
        mr_validator.main()
    assert excinfo.value.code == 2

def test_main_exit_network_failure_during_verify_auth(mocker, mr_validator):
    mock_args = mocker.MagicMock()
    mock_args.project_id = "proj"
    mock_args.mr_iid = 1
    mock_args.gitlab_url = "http://gitlab"
    mock_args.jira_url = "http://jira"
    
    mocker.patch.object(mr_validator, 'parse_args', return_value=mock_args)
    mocker.patch.object(mr_validator, 'setup_logging')
    mocker.patch('os.getenv', side_effect=lambda name, default=None: "token" if "TOKEN" in name else default)
    
    mock_gitlab = mocker.MagicMock()
    mock_gitlab.verify_auth.side_effect = requests.exceptions.ConnectionError("Connection refused")
    mocker.patch.object(mr_validator, 'GitLabClient', return_value=mock_gitlab)
    
    with pytest.raises(SystemExit) as excinfo:
        mr_validator.main()
    assert excinfo.value.code == 2

def test_main_exit_infrastructure_error_during_validate(mocker, mr_validator):
    mock_args = mocker.MagicMock()
    mock_args.project_id = "proj"
    mock_args.mr_iid = 1
    mock_args.gitlab_url = "http://gitlab"
    mock_args.jira_url = "http://jira"
    
    mocker.patch.object(mr_validator, 'parse_args', return_value=mock_args)
    mocker.patch.object(mr_validator, 'setup_logging')
    mocker.patch('os.getenv', return_value=None)
    
    mocker.patch.object(mr_validator, 'GitLabClient')
    mocker.patch.object(mr_validator, 'JiraClient')
    
    mock_validator_instance = mocker.MagicMock()
    # Simulate network crash during rule evaluation
    mock_validator_instance.validate_mr.side_effect = requests.exceptions.Timeout("Timeout calling GitLab")
    mocker.patch.object(mr_validator, 'Validator', return_value=mock_validator_instance)
    
    with pytest.raises(SystemExit) as excinfo:
        mr_validator.main()
    assert excinfo.value.code == 2

def test_entrypoint_keyboard_interrupt(mocker, mr_validator):
    # Mock main to raise KeyboardInterrupt
    mocker.patch.object(mr_validator, 'main', side_effect=KeyboardInterrupt)
    
    with pytest.raises(SystemExit) as excinfo:
        mr_validator.entrypoint()
    assert excinfo.value.code == 130

def test_entrypoint_unexpected_exception(mocker, mr_validator):
    # Mock main to raise an unexpected Exception
    mocker.patch.object(mr_validator, 'main', side_effect=RuntimeError("Some severe internal crash"))
    
    with pytest.raises(SystemExit) as excinfo:
        mr_validator.entrypoint()
    assert excinfo.value.code == 2
