import re

TICKET_REGEX = re.compile(r'WMS-\d+')
VALID_JIRA_STATES = {'In Review', 'Done'}
DEFAULT_PROJECT_ID = 'sztomi/mr-validator-homework'
MAX_RETRIES = 5
RETRY_BACKOFF_BASE = 5
REQUEST_TIMEOUT = 30
