"""
Example usage of the GenEWeb Python modernization

This script demonstrates how to use the Python GenEWeb API
to create, populate, and query a genealogical database.
"""

from datetime import date

from geneweb.core.definitions import (
    Access,
    Calendar,
    DateMY,
    Family,
    GeneDate,
    Person,
    PersonalEvent,
    PersonalEventName,
    Precision,
    RelationKind,
    Sex,
)
from geneweb.db.driver import create_database_driver
from geneweb.util.string_utils import date_to_geneweb_date


def create_sample_database():
    """Create a sample genealogical database"""

    print("Creating sample GenEWeb database...")

    # Create database
    driver = create_database_driver("sample_family.pickle", "pickle")
    if not driver.open_database(read_only=False):
        print("Failed to create database")
        return

    try:
        # Create some sample persons

        # Patriarch
        john_doe = Person(
            first_name="John",
            surname="Doe",
            occurrence=0,
            sex=Sex.MALE,
            access=Access.PUBLIC,
            birth_date=date_to_geneweb_date(date(1920, 3, 15)),
            birth_place="New York, NY, USA",
            death_place="Los Angeles, CA, USA",
            occupation="Engineer",
            notes="Emigrated from Ireland in 1919",
        )

        # Matriarch
        mary_smith = Person(
            first_name="Mary",
            surname="Smith",
            occurrence=0,
            sex=Sex.FEMALE,
            access=Access.PUBLIC,
            birth_date=date_to_geneweb_date(date(1925, 7, 22)),
            birth_place="Boston, MA, USA",
            occupation="Teacher",
            notes="Graduated from Boston University in 1947",
        )

        # Children
        robert_doe = Person(
            first_name="Robert",
            surname="Doe",
            occurrence=0,
            sex=Sex.MALE,
            access=Access.PUBLIC,
            birth_date=date_to_geneweb_date(date(1948, 12, 3)),
            birth_place="Boston, MA, USA",
            occupation="Doctor",
        )

        susan_doe = Person(
            first_name="Susan",
            surname="Doe",
            occurrence=0,
            sex=Sex.FEMALE,
            access=Access.PUBLIC,
            birth_date=date_to_geneweb_date(date(1951, 8, 17)),
            birth_place="Boston, MA, USA",
            occupation="Artist",
        )

        # Add persons to database
        john_id = driver.add_person(john_doe)
        mary_id = driver.add_person(mary_smith)
        robert_id = driver.add_person(robert_doe)
        susan_id = driver.add_person(susan_doe)

        print(f"Added {driver.get_person_count()} persons to database")

        # Create family relationships
        main_family = Family(
            marriage_date=date_to_geneweb_date(date(1947, 6, 10)),
            marriage_place="Boston, MA, USA",
            relation=RelationKind.MARRIED,
            comment="Met at Boston University",
        )

        family_id = driver.add_family(main_family)
        print(f"Added {driver.get_family_count()} families to database")

        # Set up relationships (this would be more complex in full implementation)
        from geneweb.core.definitions import Ascendants, Descendants, Union

        # Children's ascendants point to parents' family
        robert_ascendants = Ascendants(parents_family=family_id)
        susan_ascendants = Ascendants(parents_family=family_id)

        driver.set_ascendants(robert_id, robert_ascendants)
        driver.set_ascendants(susan_id, susan_ascendants)

        # Parents' union points to their family
        john_union = Union(families=[family_id])
        mary_union = Union(families=[family_id])

        driver.set_union(john_id, john_union)
        driver.set_union(mary_id, mary_union)

        # Family's descendants point to children
        family_descendants = Descendants(children=[robert_id, susan_id])
        driver.set_descendants(family_id, family_descendants)

        print("Set up family relationships")

        # Show database info
        info = driver.get_database_info()
        print(f"\\nDatabase created successfully:")
        print(f"  Name: {info.name}")
        print(f"  Persons: {info.number_of_persons}")
        print(f"  Families: {info.number_of_families}")

    finally:
        driver.close_database()


def query_sample_database():
    """Query the sample database"""

    print("\\nQuerying sample database...")

    driver = create_database_driver("sample_family.pickle", "pickle")
    if not driver.open_database():
        print("Failed to open database")
        return

    try:
        # List all persons
        print("\\nAll persons in database:")
        for person_id, person in driver.get_persons():
            birth_info = ""
            if person.birth_date:
                from geneweb.util.string_utils import geneweb_date_to_string

                birth_info = f" (born {geneweb_date_to_string(person.birth_date)})"

            print(f"  {person.first_name} {person.surname}{birth_info}")
            if person.occupation:
                print(f"    Occupation: {person.occupation}")
            if person.birth_place:
                print(f"    Birth place: {person.birth_place}")

        # Search for specific person
        print("\\nSearching for 'John':")
        results = driver.search_persons("John", 10)
        for person_id, person in results:
            print(f"  Found: {person.first_name} {person.surname}")

        # Find person by name
        print("\\nLooking up Mary Smith:")
        result = driver.find_person_by_name("Mary", "Smith")
        if result:
            person_id, person = result
            print(f"  Found: {person.first_name} {person.surname}")
            if person.notes:
                print(f"  Notes: {person.notes}")

    finally:
        driver.close_database()


def main():
    """Main example function"""
    print("GenEWeb Python Modernization - Example Usage")
    print("=" * 50)

    create_sample_database()
    query_sample_database()

    print("\\nExample completed successfully!")
    print("You can now start the web server to view this database:")
    print("  python -m geneweb.web.server --database-dir .")


if __name__ == "__main__":
    main()
