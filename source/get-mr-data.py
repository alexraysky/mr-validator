# Helper for fetching data to test out client

import argparse
import os
from dotenv import load_dotenv

from clients import GitLabClient
from helpers import DEFAULT_PROJECT_ID

def parse_args():
    parser = argparse.ArgumentParser(description="MR getter")
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
    
    return parser.parse_args()

def main():
    load_dotenv()
    args = parse_args()
    gitlab_client = GitLabClient(base_url=args.gitlab_url, token=os.getenv("GITLAB_TOKEN"))
    try:
        mr_data = gitlab_client.get_merge_request(args.project_id, args.mr_iid)
        print("\nMR Data:")
        print("Title: ", mr_data.get('title', ''))
        print("Description: ", mr_data.get('description', ''))
        print("Source Branch: ", mr_data.get('source_branch', ''))
        commits = gitlab_client.get_merge_request_commits(args.project_id, args.mr_iid)
        print("\nCommits:")
        for commit in commits:
            print("Title: ", commit.get('title', ''))
            print("Message: ", commit.get('message', ''))
    finally:
        gitlab_client.close()


if __name__ == "__main__":
    main()
