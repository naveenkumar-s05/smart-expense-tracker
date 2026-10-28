# Test configuration
import os
import tempfile

# Use temp db for tests
TEST_DB_PATH = None


def get_test_db():
    global TEST_DB_PATH
    if TEST_DB_PATH is None:
        fd, TEST_DB_PATH = tempfile.mkstemp(suffix='.db')
        os.close(fd)
    return TEST_DB_PATH
