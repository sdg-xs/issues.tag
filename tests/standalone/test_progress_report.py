"""Progress replacement survives transient locks without hiding persistent failures."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from verification_progress import replace_progress


class ProgressReportTests(unittest.TestCase):
    def lock_error(self):
        error = PermissionError('Locked by a reader')
        error.winerror = 5
        return error

    @patch('verification_progress.time.sleep')
    def test_transient_lock_retries_same_atomic_replacement(self, sleep):
        temporary = Mock()
        temporary.replace.side_effect = [self.lock_error(), self.lock_error(), None]
        replace_progress(temporary, 'progress.json')
        self.assertEqual(temporary.replace.call_count, 3)
        temporary.replace.assert_called_with('progress.json')
        self.assertEqual(sleep.call_count, 2)

    @patch('verification_progress.time.sleep')
    def test_persistent_lock_remains_a_failure(self, sleep):
        temporary = Mock()
        temporary.replace.side_effect = self.lock_error()
        with self.assertRaises(PermissionError):
            replace_progress(temporary, 'progress.json')
        self.assertEqual(temporary.replace.call_count, 10)

    @patch('verification_progress.time.sleep')
    def test_other_permission_failure_is_not_retried(self, sleep):
        temporary = Mock()
        temporary.replace.side_effect = PermissionError('Other permission failure')
        with self.assertRaises(PermissionError):
            replace_progress(temporary, 'progress.json')
        sleep.assert_not_called()


if __name__ == '__main__':
    unittest.main()
