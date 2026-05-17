import sys
import requests
from helpers.logging_config import logger

def verify_connections(gitlab_token, gitlab_client, gitlab_url, jira_token, jira_client, jira_url):
    """Verifies tokens and connectivity for GitLab and Jira clients."""
    if gitlab_token:
        logger.debug("Verifying GitLab token...")
        try:
            if not gitlab_client.verify_auth():
                logger.error("[FAIL] GitLab token is invalid or expired.")
                sys.exit(2)
            else:
                logger.debug("GitLab token successfully verified.")
        except requests.exceptions.RequestException as e:
            logger.error(f"[FAIL] Could not connect to GitLab at {gitlab_url}: {e}")
            sys.exit(2)

    if jira_token:
        logger.debug("Verifying Jira token...")
        try:
            if not jira_client.verify_auth():
                logger.error("[FAIL] Jira token is invalid or expired.")
                sys.exit(2)
            else:
                logger.debug("Jira token successfully verified.")
        except requests.exceptions.RequestException as e:
            logger.error(f"[FAIL] Could not connect to Jira at {jira_url}: {e}")
            sys.exit(2)
