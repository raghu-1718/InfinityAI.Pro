import unittest
import sys
import logging

from backend.shared.utils import validators

class TestPlaceholderGuard(unittest.TestCase):

    def test_valid_value_passes(self):
        # Should return True and not exit
        self.assertTrue(validators.assert_no_placeholder('TEST_NAME', 'real_value_123'))

    def test_empty_value_exits(self):
        with self.assertRaises(SystemExit):
            validators.assert_no_placeholder('TEST_NAME', '')

    def test_placeholder_value_exits(self):
        with self.assertRaises(SystemExit):
            validators.assert_no_placeholder('TEST_NAME', 'PLACEHOLDER_ACCESS_TOKEN')

    def test_variant_sentinel_exits(self):
        with self.assertRaises(SystemExit):
            validators.assert_no_placeholder('TEST_NAME', 'dummy')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
