import unittest
from unittest.mock import MagicMock, patch
from source.helpers import with_retries
from source.constants import MAX_RETRIES, RETRY_BACKOFF_BASE

class TestRetries(unittest.TestCase):
    
    @patch('time.sleep', return_value=None) # Don't actually sleep
    def test_with_retries_success_eventually(self, mock_sleep):
        # Function that fails twice then succeeds
        mock_func = MagicMock()
        mock_func.side_effect = [Exception("Fail 1"), Exception("Fail 2"), "Success"]
        
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
        mock_func.side_effect = Exception("Permanent Fail")
        
        decorated_func = with_retries(mock_func)
        
        with self.assertRaises(Exception) as cm:
            decorated_func()
        
        self.assertEqual(str(cm.exception), "Permanent Fail")
        # MAX_RETRIES is 5, so total 6 attempts
        self.assertEqual(mock_func.call_count, MAX_RETRIES + 1)
        self.assertEqual(mock_sleep.call_count, MAX_RETRIES)

if __name__ == '__main__':
    unittest.main()
