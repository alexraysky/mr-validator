import re
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor
from gitlab_client import GitLabClient
from jira_client import JiraClient

CODE_BLOCK_RE = re.compile(r'```[\s\S]*?```')
INLINE_CODE_RE = re.compile(r'`[^`]*?`')

class Validator:

    def __init__(self, gitlab_client: GitLabClient, jira_client: JiraClient, ticket_regex: re.Pattern, valid_jira_states: set):
        self.gitlab = gitlab_client
        self.jira = jira_client
        self.ticket_regex = ticket_regex
        self.valid_jira_states = valid_jira_states

    def _strip_code_blocks(self, text: str) -> str:
        """Remove Markdown code blocks and inline code from text."""
        if not text:
            return ""
        # Remove multi-line code blocks (```...```)
        text = CODE_BLOCK_RE.sub('', text)
        # Remove inline code blocks (`...`)
        text = INLINE_CODE_RE.sub('', text)
        return text

    def extract_tickets(self, mr_data: dict, commits: list) -> set:
        """Extract all unique Jira tickets from MR title, description, branch, and commits."""
        if not isinstance(mr_data, dict):
            mr_data = {}
        if not isinstance(commits, list):
            commits = []
            
        text_sources = [
            mr_data.get('title') or '',
            mr_data.get('description') or '',
            mr_data.get('source_branch') or ''
        ]
        
        for commit in commits:
            if isinstance(commit, dict):
                text_sources.append(commit.get('title') or '')
                text_sources.append(commit.get('message') or '')
            
        # Strip code blocks from each source to avoid false positives
        cleaned_sources = [self._strip_code_blocks(text) for text in text_sources if text]
        combined_text = " ".join(cleaned_sources)
        return set(self.ticket_regex.findall(combined_text))

    def validate_mr(self, project_id: str, mr_iid: int) -> Tuple[bool, List[str]]:
        """
        Validates the MR against all rules.
        Returns a tuple: (passed: bool, output_messages: list of str)
        """
        import requests
        messages = []
        passed = True

        try:
            mr_data = self.gitlab.get_merge_request(project_id, mr_iid)
            commits = self.gitlab.get_merge_request_commits(project_id, mr_iid)
        except requests.exceptions.RequestException:
            # Let actual connection/timeout/network errors bubble up
            raise
        except Exception as e:
            messages.append(f"[FAIL] Could not fetch MR data from GitLab: {e}")
            return False, messages

        # Rule 1: Draft state
        is_draft = mr_data.get('draft', False)
        if is_draft:
            messages.append("[FAIL] Rule 1: MR is in Draft state.")
            passed = False
        else:
            messages.append("[PASS] Rule 1: MR is not in Draft state.")

        # Rule 2: Ticket reference
        tickets = self.extract_tickets(mr_data, commits)
        if not tickets:
            messages.append("[FAIL] Rule 2: MR references zero Jira tickets.")
            passed = False
        else:
            messages.append(f"[PASS] Rule 2: MR references Jira tickets: {', '.join(tickets)}.")

        # If no tickets, we skip Rules 3 and 4
        if not tickets:
            return passed, messages

        # Rules 3 & 4
        def fetch_issue(ticket):
            try:
                return ticket, self.jira.get_issue(ticket), None
            except Exception as e:
                return ticket, None, e

        with ThreadPoolExecutor(max_workers=min(len(tickets), 5)) as executor:
            results = list(executor.map(fetch_issue, tickets))

        for ticket, issue, exc in results:
            if exc is not None:
                if isinstance(exc, requests.exceptions.RequestException):
                    # Let actual connection/timeout/network errors bubble up
                    raise exc
                messages.append(f"[FAIL] Error validating Jira ticket {ticket}: {exc}")
                passed = False
                continue

            # Rule 3: Exists
            if not issue:
                messages.append(f"[FAIL] Rule 3: Referenced Jira ticket {ticket} doesn't exist.")
                passed = False
                continue
            else:
                messages.append(f"[PASS] Rule 3: Jira ticket {ticket} exists.")

            # Rule 4: Status
            status_name = issue.get('fields', {}).get('status', {}).get('name', 'Unknown')
            if status_name not in self.valid_jira_states:
                messages.append(f"[FAIL] Rule 4: Jira ticket {ticket} is in invalid state '{status_name}'. Allowed states: {', '.join(self.valid_jira_states)}.")
                passed = False
            else:
                messages.append(f"[PASS] Rule 4: Jira ticket {ticket} is in valid state '{status_name}'.")

        return passed, messages
