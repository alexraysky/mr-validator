import pytest
import logging
import json
import sys
from source.logging_config import ColorFormatter, setup_logging, logger
from source.helpers import print_red, print_green, print_yellow

def test_color_formatter_adds_ansi_escape_codes():
    formatter_color = ColorFormatter(use_color=True)
    formatter_plain = ColorFormatter(use_color=False)
    
    # Test INFO log record that starts with [PASS]
    record_pass = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="[PASS] Rule 1 passed", args=(), exc_info=None
    )
    
    formatted_color = formatter_color.format(record_pass)
    formatted_plain = formatter_plain.format(record_pass)
    
    assert "\033[92m" in formatted_color  # ANSI green code present
    assert "\033[0m" in formatted_color   # ANSI reset code present
    assert "\033[92m" not in formatted_plain
    assert "\033[0m" not in formatted_plain

def test_color_formatter_handles_error():
    formatter_color = ColorFormatter(use_color=True)
    
    record_error = logging.LogRecord(
        name="test", level=logging.ERROR, pathname="", lineno=0,
        msg="Unexpected error occurred", args=(), exc_info=None
    )
    
    formatted_color = formatter_color.format(record_error)
    assert "\033[91m" in formatted_color  # ANSI red code present

def test_setup_logging_levels():
    # Test verbose sets DEBUG level and has timestamps
    setup_logging(verbose=True, quiet=False, force_color=False)
    assert logger.level == logging.DEBUG
    
    # Test quiet sets ERROR level
    setup_logging(verbose=False, quiet=True, force_color=False)
    assert logger.level == logging.ERROR
    
    # Test default sets INFO level
    setup_logging(verbose=False, quiet=False, force_color=False)
    assert logger.level == logging.INFO

def test_helpers_delegate_to_logger(mocker):
    mock_info = mocker.patch.object(logger, 'info')
    mock_warning = mocker.patch.object(logger, 'warning')
    mock_error = mocker.patch.object(logger, 'error')
    
    print_green("Green msg")
    mock_info.assert_called_once_with("Green msg")
    
    print_yellow("Yellow msg")
    mock_warning.assert_called_once_with("Yellow msg")
    
    print_red("Red msg")
    mock_error.assert_called_once_with("Red msg")

def test_json_format_output(mocker, capsys):
    import importlib
    mr_validator = importlib.import_module("source.mr-validator")

    # Mock parse_args to return JSON output settings
    mock_args = mocker.MagicMock()
    mock_args.project_id = "test-project"
    mock_args.mr_iid = 5
    mock_args.gitlab_url = "http://gitlab"
    mock_args.jira_url = "http://jira"
    mocker.patch.object(mr_validator, 'parse_args', return_value=mock_args)
    
    # Force setup_logging to not fail on TTY issues
    mocker.patch.object(mr_validator, 'setup_logging')
    
    # Mock clients and validator
    mock_gitlab = mocker.patch.object(mr_validator, 'GitLabClient')
    mock_jira = mocker.patch.object(mr_validator, 'JiraClient')
    
    mock_validator_instance = mocker.MagicMock()
    mock_validator_instance.validate_mr.return_value = (True, ["[PASS] Rule 1", "[PASS] Rule 2"])
    mocker.patch.object(mr_validator, 'Validator', return_value=mock_validator_instance)
    
    # Mock sys.exit to prevent test runner from exiting
    mock_exit = mocker.patch('sys.exit')
    
    # Run text format first
    mock_args.output_format = "text"
    mr_validator.main()
    mock_exit.assert_called_with(0)
    
    # Run JSON format
    mock_args.output_format = "json"
    mr_validator.main()
    mock_exit.assert_called_with(0)
    
    # Check that stdout has valid JSON in the final call
    captured = capsys.readouterr()
    json_output = None
    for line in captured.out.splitlines():
        if line.strip().startswith("{"):
            json_output = line
            # Consume remainder of stream to get full json block
            idx = captured.out.find(line)
            json_output = captured.out[idx:]
            break
            
    assert json_output is not None
    data = json.loads(json_output)
    assert data["passed"] is True
    assert data["project_id"] == "test-project"
    assert data["mr_iid"] == 5
    assert "[PASS] Rule 1" in data["messages"]
