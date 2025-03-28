"""Тесты для core.py"""
import unittest
from project_name.core import main
class TestCore(unittest.TestCase):
    def test_main(self):
        self.assertIsNone(main())
if __name__ == "__main__":
    unittest.main()
