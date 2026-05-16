import argparse
import os
import sys
import json
from dotenv import load_dotenv

from gitlab_client import GitLabClient
from jira_client import JiraClient
from validator import Validator
from constants import TICKET_REGEX, VALID_JIRA_STATES, DEFAULT_PROJECT_ID
from helpers import *
from logging_config import setup_logging, logger


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


def main():
    load_dotenv()

    args = parse_args()

    # Initialize structured logging
    setup_logging(verbose=args.verbose, quiet=args.quiet)

    # get tokens from env
    gitlab_token = os.getenv("GITLAB_TOKEN")
    jira_token = os.getenv("JIRA_TOKEN")

    # init clients
    gitlab_client = GitLabClient(base_url=args.gitlab_url, token=gitlab_token)
    jira_client = JiraClient(base_url=args.jira_url, token=jira_token)

    # init validator
    validator = Validator(
        gitlab_client=gitlab_client,
        jira_client=jira_client,
        ticket_regex=TICKET_REGEX,
        valid_jira_states=VALID_JIRA_STATES
    )

    # do the validation
    logger.info(f"Validating MR !{args.mr_iid} for project {args.project_id}...")
    passed, messages = validator.validate_mr(args.project_id, args.mr_iid)

    # Output results based on format
    if args.output_format == "json":
        result = {
            "passed": passed,
            "project_id": args.project_id,
            "mr_iid": args.mr_iid,
            "messages": messages
        }
        # Print JSON document cleanly to stdout
        print(json.dumps(result, indent=2))
        sys.exit(0 if passed else 1)
    else:
        # print text results via logger
        logger.info("")
        logger.info("--- Validation Summary ---")
        for msg in messages:
            if msg.startswith("[PASS]"):
                print_green(msg)
            elif msg.startswith("[FAIL]"):
                print_red(msg)
            else:
                logger.info(msg)
        logger.info("--------------------------")
        if passed:
            print_green("Result: PASS. MR can be merged.")
            sys.exit(0)
        else:
            print_red("Result: FAIL. MR does not meet requirements.")
            sys.exit(1)

if __name__ == "__main__":
    main()

