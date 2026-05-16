import argparse
import os
import sys
from dotenv import load_dotenv

from gitlab_client import GitLabClient
from jira_client import JiraClient
from validator import Validator
from constants import TICKET_REGEX, VALID_JIRA_STATES, DEFAULT_PROJECT_ID
from helpers import *


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
    
    return parser.parse_args()


def main():
    load_dotenv()

    args = parse_args()

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
    print(f"Validating MR !{args.mr_iid} for project {args.project_id}...")
    passed, messages = validator.validate_mr(args.project_id, args.mr_iid)

    # print results
    print("\n--- Validation Summary ---")
    for msg in messages:
        if msg.startswith("[PASS]"):
            print_green(msg)
        elif msg.startswith("[FAIL]"):
            print_red(msg)
        else:
            print(msg)
    print("--------------------------")
    if passed:
        print_green("Result: PASS. MR can be merged.")
        sys.exit(0)
    else:
        print_red("Result: FAIL. MR does not meet requirements.")
        sys.exit(1)

if __name__ == "__main__":
    main()
