from unittest import TestCase
from functions.hashing.hashing import *


class MongoTests(TestCase):

    def test_hashing_matches(self):
        # check hashing compare right password works
        test_hash = hash_secret("test")
        secret_matches = check_secret_matches("test", test_hash)
        self.assertTrue(secret_matches)

    def test_hashing_does_not_matches(self):
        # check hashing compare right password works
        test_hash = hash_secret("test")
        secret_matches = check_secret_matches("a_wrong_value", test_hash)
        self.assertFalse(secret_matches)
