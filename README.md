# MR Pre-Merge Validator

This is a Python CLI tool that acts as a CI/CD pre-merge gate. It checks a GitLab Merge Request to ensure it meets specific Jira ticket rules before it can be merged.

## Rules
For a given MR, the tool exits with `1` (fail) if ANY of the following are true:
1. The MR is in **Draft** state.
2. The MR references **zero** Jira tickets (checked across MR title, source branch name, description, and commit messages).
3. The MR references a ticket that **doesn’t exist** in Jira.
4. Any referenced ticket is **not** in state `In Review` or `Done`.

Otherwise, it exits with `0` (pass).

## Requirements
- Python 3.9+
- `pip`

## Installation

```bash
python -m venv .venv
# Activate the venv:
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r source/requirements.txt
```

## Usage

You can run the CLI with standard arguments:

```bash
cd source
python mr-validator.py --project-id sztomi/mr-validator-homework --mr-iid 1
```

### Environment Variables
For convenience, particularly in a CI environment, you can set the following environment variables (or place them in a `.env` file in the root):

- `GITLAB_URL` (default: `https://gitlab.com`)
- `GITLAB_TOKEN` (optional: Personal Access Token for GitLab if validating private repositories)
- `JIRA_BASE_URL` (default: `http://localhost:8080` for the mock Jira server)
- `JIRA_TOKEN` (optional: Bearer token for real Jira API)

### Example with mock Jira
1. In one terminal, start the mock Jira server:
   ```bash
   python mocks/mock_jira.py
   ```
2. In another terminal, run the validator against the public repository:
   ```bash
   cd source
   python mr-validator.py --project-id sztomi/mr-validator-homework --mr-iid 1
   ```

## Running Tests

Automated tests are written with `pytest`. To run them:

```bash
pytest tests/
```
