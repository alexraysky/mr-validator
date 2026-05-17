import argparse
import os
import sys
import json
import logging
import signal
import requests
from dotenv import load_dotenv

from clients import GitLabClient, JiraClient
from core import Validator, post_results
from helpers import TICKET_REGEX, VALID_JIRA_STATES, DEFAULT_PROJECT_ID
from helpers import setup_logging, logger, verify_connections


def parse_args():
    parser = argparse.ArgumentParser(description="MR Pre-Merge Validator")
    parser.add_argument(
        "--project-id", 
        default=DEFAULT_PROJECT_ID, 
        help="GitLab Project ID or Path (e.g. sztomi/mr-validator-homework)"
    )
    parser.add_argument(
        "--mr-iid", 
        required=True, 
        type=int, 
        help="Merge Request IID"
    )
    parser.add_argument(
        "--gitlab-url", 
        default=os.getenv("GITLAB_URL", "https://gitlab.com"), 
        help="GitLab Base URL"
    )
    parser.add_argument(
        "--jira-url", 
        default=os.getenv("JIRA_BASE_URL", "http://localhost:8080"), 
        help="Jira Base URL"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable detailed verbose logging"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Only log errors"
    )
    parser.add_argument(
        "--output-format", "-f",
        choices=["text", "json"],
        default="text",
        help="Select the output format (text or json)"
    )
    
    return parser.parse_args()


def handle_sigterm(signum, frame):
    logger.error("Received SIGTERM signal. Shutting down gracefully.")
    sys.exit(130)


def do_validate():
    # Register SIGTERM signal handler
    signal.signal(signal.SIGTERM, handle_sigterm)

    load_dotenv()

    args = parse_args()

    # Initialize structured logging
    setup_logging(verbose=args.verbose, quiet=args.quiet)

    # get tokens from env
    gitlab_token = os.getenv("GITLAB_TOKEN")
    jira_token = os.getenv("JIRA_TOKEN")

    if not gitlab_token:
        logger.warning("GITLAB_TOKEN environment variable is not set. Public repository access only.")
    if not jira_token:
        logger.warning("JIRA_TOKEN environment variable is not set. Unauthenticated Jira requests will be sent.")

    # init clients
    gitlab_client = GitLabClient(base_url=args.gitlab_url, token=gitlab_token)
    jira_client = JiraClient(base_url=args.jira_url, token=jira_token)

    try:
        # Startup Token/Connection Verification
        verify_connections(
            gitlab_token=gitlab_token,
            gitlab_client=gitlab_client,
            gitlab_url=args.gitlab_url,
            jira_token=jira_token,
            jira_client=jira_client,
            jira_url=args.jira_url
        )

        # init validator
        validator = Validator(
            gitlab_client=gitlab_client,
            jira_client=jira_client,
            ticket_regex=TICKET_REGEX,
            valid_jira_states=VALID_JIRA_STATES
        )

        # do the validation
        logger.info(f"Validating MR !{args.mr_iid} for project {args.project_id}...")
        try:
            passed, messages = validator.validate_mr(args.project_id, args.mr_iid)
        except requests.exceptions.RequestException as e:
            logger.error(f"[FAIL] Infrastructure/Connection error calling GitLab/Jira APIs: {e}")
            sys.exit(2)

        # Output results based on format
        post_results(args, passed, messages)

        sys.exit(0 if passed else 1)    
    finally:
        gitlab_client.close()
        jira_client.close()


def main():
    try:
        do_validate()
    except KeyboardInterrupt:
        logger.error("\nExecution interrupted by user (Ctrl+C). Exiting.")
        sys.exit(130)
    except Exception as e:
        logger.critical(f"[FATAL] Unexpected error: {e}", exc_info=logger.isEnabledFor(logging.DEBUG))
        sys.exit(2)


if __name__ == "__main__":
    main()


