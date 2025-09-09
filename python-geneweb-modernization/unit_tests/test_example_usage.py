"""
Unit tests for example_usage.py
"""

import os
import pytest
from datetime import date
import shutil
from example_usage import create_sample_database, query_sample_database

@pytest.fixture
def setup_teardown():
    """Setup and teardown for tests"""
    # Setup - Make sure we have a clean state
    if os.path.exists("sample_family.pickle"):
        os.remove("sample_family.pickle")
    
    yield
    
    # Teardown - Clean up after tests
    if os.path.exists("sample_family.pickle"):
        os.remove("sample_family.pickle")
    if os.path.exists("sample_family.pickle.backup"):
        os.remove("sample_family.pickle.backup")

def test_create_sample_database(setup_teardown):
    """Test creation of sample database"""
    # Execute
    create_sample_database()
    
    # Verify
    assert os.path.exists("sample_family.pickle"), "Database file was not created"

def test_query_sample_database(setup_teardown, capsys):
    """Test querying the sample database"""
    # Setup
    create_sample_database()
    
    # Execute
    query_sample_database()
    
    # Capture output
    captured = capsys.readouterr()
    
    # Verify key information is present in output
    assert "John Doe" in captured.out, "John Doe not found in output"
    assert "Mary Smith" in captured.out, "Mary Smith not found in output"
    assert "Robert Doe" in captured.out, "Robert Doe not found in output"
    assert "Susan Doe" in captured.out, "Susan Doe not found in output"
    
    # Verify occupation info
    assert "Engineer" in captured.out, "John's occupation not found"
    assert "Teacher" in captured.out, "Mary's occupation not found"
    
    # Verify birth places
    assert "New York, NY, USA" in captured.out, "John's birth place not found"
    assert "Boston, MA, USA" in captured.out, "Mary's birth place not found"

if __name__ == "__main__":
    pytest.main(["-v"])