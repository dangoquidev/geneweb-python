"""
Basic tests for GenEWeb Python modernization

These tests verify that the core functionality works correctly
and maintains compatibility with the original GenEWeb concepts.
"""

import unittest
import tempfile
import os
from datetime import date

from geneweb.core.definitions import (
    Person, Family, GeneDate, DateMY, Precision, Calendar,
    Sex, Access, RelationKind, HttpStatus
)
from geneweb.core.config import Config
from geneweb.db.driver import create_database_driver
from geneweb.util.string_utils import (
    normalize_name, compare_names, date_to_geneweb_date, 
    geneweb_date_to_string, calculate_age
)
from geneweb.security import create_security_manager, AccessLevel


class TestCoreDefinitions(unittest.TestCase):
    """Test core data structures and definitions"""
    
    def test_person_creation(self):
        """Test creating a person"""
        person = Person(
            first_name="John",
            surname="Doe",
            occurrence=0,
            sex=Sex.MALE,
            access=Access.PUBLIC
        )
        
        self.assertEqual(person.first_name, "John")
        self.assertEqual(person.surname, "Doe")
        self.assertEqual(person.sex, Sex.MALE)
        self.assertEqual(person.access, Access.PUBLIC)
    
    def test_family_creation(self):
        """Test creating a family"""
        family = Family(
            marriage_place="New York",
            relation=RelationKind.MARRIED
        )
        
        self.assertEqual(family.marriage_place, "New York")
        self.assertEqual(family.relation, RelationKind.MARRIED)
    
    def test_geneweb_date(self):
        """Test GenEWeb date structures"""
        # Test creating date from Python date
        python_date = date(1950, 3, 15)
        gw_date = date_to_geneweb_date(python_date)
        
        self.assertIsNotNone(gw_date.gregorian_date)
        dmy, calendar = gw_date.gregorian_date
        self.assertEqual(dmy.year, 1950)
        self.assertEqual(dmy.month, 3)
        self.assertEqual(dmy.day, 15)
        self.assertEqual(calendar, Calendar.GREGORIAN)
        
        # Test converting back to string
        date_str = geneweb_date_to_string(gw_date)
        self.assertIn("1950", date_str)
        self.assertIn("3", date_str)
        self.assertIn("15", date_str)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_name_normalization(self):
        """Test name normalization"""
        # Test that apostrophes and spaces are normalized consistently
        self.assertEqual(normalize_name("O'Connor"), normalize_name("O Connor"))
        self.assertEqual(normalize_name("José María"), normalize_name("jose maria"))
        self.assertTrue(compare_names("Smith", "SMITH"))
        self.assertTrue(compare_names("O'Reilly", "O REILLY"))
    
    def test_age_calculation(self):
        """Test age calculation"""
        birth_date = date_to_geneweb_date(date(1950, 1, 1))
        reference_date = date_to_geneweb_date(date(2000, 1, 1))
        
        age = calculate_age(birth_date, reference_date)
        self.assertEqual(age, 50)
        
        # Test with birthday not yet occurred
        reference_date = date_to_geneweb_date(date(1999, 12, 31))
        age = calculate_age(birth_date, reference_date)
        self.assertEqual(age, 49)


class TestDatabaseDriver(unittest.TestCase):
    """Test database operations"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.pickle")
        self.driver = create_database_driver(self.db_path, "pickle")
        self.assertTrue(self.driver.open_database(read_only=False))
    
    def tearDown(self):
        """Clean up test database"""
        self.driver.close_database()
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_add_person(self):
        """Test adding a person to database"""
        person = Person(
            first_name="John",
            surname="Doe",
            occurrence=0,
            sex=Sex.MALE,
            access=Access.PUBLIC
        )
        
        person_id = self.driver.add_person(person)
        self.assertIsNotNone(person_id)
        
        # Retrieve person
        retrieved_person = self.driver.get_person(person_id)
        self.assertIsNotNone(retrieved_person)
        self.assertEqual(retrieved_person.first_name, "John")
        self.assertEqual(retrieved_person.surname, "Doe")
    
    def test_find_person_by_name(self):
        """Test finding person by name"""
        person = Person(
            first_name="Mary",
            surname="Smith",
            occurrence=0,
            sex=Sex.FEMALE
        )
        
        person_id = self.driver.add_person(person)
        
        # Find by name
        result = self.driver.find_person_by_name("Mary", "Smith")
        self.assertIsNotNone(result)
        
        found_id, found_person = result
        self.assertEqual(found_id, person_id)
        self.assertEqual(found_person.first_name, "Mary")
    
    def test_search_persons(self):
        """Test searching persons"""
        # Add test persons
        persons = [
            Person(first_name="John", surname="Smith", occurrence=0, sex=Sex.MALE),
            Person(first_name="Jane", surname="Smith", occurrence=0, sex=Sex.FEMALE),
            Person(first_name="Bob", surname="Jones", occurrence=0, sex=Sex.MALE)
        ]
        
        for person in persons:
            self.driver.add_person(person)
        
        # Search for "Smith"
        results = self.driver.search_persons("Smith")
        self.assertEqual(len(results), 2)
        
        # Search for "John"
        results = self.driver.search_persons("John")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1].first_name, "John")
    
    def test_database_info(self):
        """Test getting database information"""
        info = self.driver.get_database_info()
        self.assertIsNotNone(info)
        self.assertEqual(info.number_of_persons, 0)
        self.assertEqual(info.number_of_families, 0)
        
        # Add a person and check count
        person = Person(first_name="Test", surname="Person", occurrence=0)
        self.driver.add_person(person)
        
        info = self.driver.get_database_info()
        self.assertEqual(info.number_of_persons, 1)


class TestConfiguration(unittest.TestCase):
    """Test configuration management"""
    
    def test_config_creation(self):
        """Test creating configuration"""
        config = Config()
        self.assertIsNotNone(config)
        self.assertEqual(config.charset, "UTF-8")
        self.assertEqual(config.private_years, 150)
    
    def test_config_access_checks(self):
        """Test access permission checks"""
        config = Config()
        
        # Test visitor access
        self.assertFalse(config.is_authenticated_user())
        self.assertFalse(config.has_full_access())
        self.assertFalse(config.can_edit())
        
        # Test wizard access
        config.wizard = True
        self.assertTrue(config.is_authenticated_user())
        self.assertTrue(config.has_full_access())
        self.assertTrue(config.can_edit())
        
        # Test friend access
        config.wizard = False
        config.friend = True
        self.assertTrue(config.is_authenticated_user())
        self.assertFalse(config.has_full_access())
        self.assertFalse(config.can_edit())


class TestSecurity(unittest.TestCase):
    """Test security and authentication"""
    
    def setUp(self):
        """Set up security manager"""
        config = Config()
        self.security_manager = create_security_manager(config)
    
    def test_add_and_authenticate_user(self):
        """Test adding and authenticating a user"""
        # Add user
        success = self.security_manager.add_user(
            "testuser", "testpass123", AccessLevel.FRIEND, "Test User"
        )
        self.assertTrue(success)
        
        # Authenticate user
        result = self.security_manager.authenticate_basic("testuser", "testpass123", "127.0.0.1")
        self.assertTrue(result.success)
        self.assertIsNotNone(result.user)
        self.assertEqual(result.user.username, "testuser")
        self.assertEqual(result.user.access_level, AccessLevel.FRIEND)
    
    def test_invalid_authentication(self):
        """Test authentication with invalid credentials"""
        result = self.security_manager.authenticate_basic("invalid", "invalid", "127.0.0.1")
        self.assertFalse(result.success)
        self.assertIsNone(result.user)
    
    def test_session_token(self):
        """Test session token creation and verification"""
        # Add user first
        self.security_manager.add_user("sessiontest", "pass123", AccessLevel.WIZARD)
        
        # Create session token
        token = self.security_manager.create_session_token("sessiontest")
        self.assertIsNotNone(token)
        
        # Verify token
        username = self.security_manager.verify_session_token(token)
        self.assertEqual(username, "sessiontest")
        
        # Revoke token
        revoked = self.security_manager.revoke_session_token(token)
        self.assertTrue(revoked)
        
        # Verify revoked token fails
        username = self.security_manager.verify_session_token(token)
        self.assertIsNone(username)


def run_tests():
    """Run all tests"""
    print("Running GenEWeb Python Modernization Tests")
    print("=" * 50)
    
    # Create test suite
    test_classes = [
        TestCoreDefinitions,
        TestUtilityFunctions, 
        TestDatabaseDriver,
        TestConfiguration,
        TestSecurity
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("All tests passed successfully!")
        print("GenEWeb Python modernization core functionality is working correctly.")
    else:
        print(f"Tests completed with {len(result.failures)} failures and {len(result.errors)} errors.")
        return False
    
    return True


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
