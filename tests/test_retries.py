import unittest
import requests
from unittest.mock import MagicMock, patch
from source.helpers import with_retries, MAX_RETRIES, RETRY_BACKOFF_BASE

class TestRetries(unittest.TestCase):
    
    @patch('time.sleep', return_value=None) # Don't actually sleep
    def test_with_retries_success_eventually(self, mock_sleep):
        # Function that fails twice then succeeds
        mock_func = MagicMock()
        mock_func.side_effect = [
            requests.exceptions.ConnectionError("Fail 1"),
            requests.exceptions.ConnectionError("Fail 2"),
            "Success"
        ]
        
        decorated_func = with_retries(mock_func)
        result = decorated_func()
        
        self.assertEqual(result, "Success")
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
        
        # Verify backoff values: pow(base, retry_number)
        # Retry 1: i=0 -> wait_time = pow(base, 1)
        # Retry 2: i=1 -> wait_time = pow(base, 2)
        mock_sleep.assert_any_call(pow(RETRY_BACKOFF_BASE, 1))
        mock_sleep.assert_any_call(pow(RETRY_BACKOFF_BASE, 2))

    @patch('time.sleep', return_value=None)
    def test_with_retries_all_fail(self, mock_sleep):
        mock_func = MagicMock()
        mock_func.side_effect = requests.exceptions.ConnectionError("Permanent Fail")
        
        decorated_func = with_retries(mock_func)
        
        with self.assertRaises(requests.exceptions.ConnectionError) as cm:
            decorated_func()
        
        self.assertEqual(str(cm.exception), "Permanent Fail")
        # MAX_RETRIES is 5, so total 6 attempts
        self.assertEqual(mock_func.call_count, MAX_RETRIES + 1)
        self.assertEqual(mock_sleep.call_count, MAX_RETRIES)

    @patch('time.sleep', return_value=None)
    def test_with_retries_non_retriable_client_error(self, mock_sleep):
        mock_func = MagicMock()
        response = MagicMock(status_code=403, headers={})
        mock_func.side_effect = requests.exceptions.HTTPError("Forbidden", response=response)
        
        decorated_func = with_retries(mock_func)
        
        with self.assertRaises(requests.exceptions.HTTPError):
            decorated_func()
        
        self.assertEqual(mock_func.call_count, 1)
        self.assertEqual(mock_sleep.call_count, 0)

    @patch('time.sleep', return_value=None)
    def test_with_retries_retriable_server_error(self, mock_sleep):
        mock_func = MagicMock()
        response = MagicMock(status_code=503, headers={})
        mock_func.side_effect = [
            requests.exceptions.HTTPError("Service Unavailable", response=response),
            "Success"
        ]
        
        decorated_func = with_retries(mock_func)
        result = decorated_func()
        
        self.assertEqual(result, "Success")
        self.assertEqual(mock_func.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch('time.sleep', return_value=None)
    def test_with_retries_429_rate_limit_with_retry_after(self, mock_sleep):
        mock_func = MagicMock()
        response = MagicMock(status_code=429, headers={"Retry-After": "42"})
        mock_func.side_effect = [
            requests.exceptions.HTTPError("Too Many Requests", response=response),
            "Success"
        ]
        
        decorated_func = with_retries(mock_func)
        result = decorated_func()
        
        self.assertEqual(result, "Success")
        self.assertEqual(mock_func.call_count, 2)
        mock_sleep.assert_called_once_with(42)

    @patch('time.sleep', return_value=None)
    def test_with_retries_non_requests_exception(self, mock_sleep):
        mock_func = MagicMock()
        mock_func.side_effect = ValueError("Programming bug")
        
        decorated_func = with_retries(mock_func)
        
        with self.assertRaises(ValueError):
            decorated_func()
        
        self.assertEqual(mock_func.call_count, 1)
        self.assertEqual(mock_sleep.call_count, 0)

if __name__ == '__main__':
    unittest.main()
