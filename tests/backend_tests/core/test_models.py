"""
Tests pour les modèles de domaine (core/models.py).

Tests de base couvrant les fonctionnalités essentielles.
"""

from datetime import date as python_date

from backend.core.enums import DatePrecision, DeathType, DivorceType, EventType, MarriageType, Sex
from backend.core.models import Date, Event, Family, Note, Person, Source

# ============================================================================
# Tests pour Date
# ============================================================================


class TestDate:
    """Tests pour la classe Date."""

    def test_date_complete(self):
        """Test création d'une date complète."""
        d = Date(day=15, month=3, year=1950)
        assert d.day == 15
        assert d.month == 3
        assert d.year == 1950
        assert d.precision == DatePrecision.EXACT
        assert d.is_complete()

    def test_date_year_only(self):
        """Test date avec année seule."""
        d = Date(year=1950)
        assert d.year == 1950
        assert d.day is None
        assert d.month is None
        assert not d.is_complete()

    def test_date_string_representation(self):
        """Test représentation textuelle des dates."""
        assert str(Date(day=15, month=3, year=1950)) == "15/03/1950"
        assert str(Date(year=1950)) == "1950"
        assert str(Date(month=3, year=1950)) == "03/1950"

    def test_date_precision_about(self):
        """Test date avec précision 'environ'."""
        d = Date(year=1950, precision=DatePrecision.ABOUT)
        assert str(d) == "~1950"

    def test_date_precision_before(self):
        """Test date avec précision 'avant'."""
        d = Date(year=1950, precision=DatePrecision.BEFORE)
        assert str(d) == "<1950"

    def test_date_precision_after(self):
        """Test date avec précision 'après'."""
        d = Date(year=1950, precision=DatePrecision.AFTER)
        assert str(d) == ">1950"

    def test_date_to_python_date(self):
        """Test conversion vers date Python."""
        d = Date(day=15, month=3, year=1950)
        py_date = d.to_python_date()
        assert py_date == python_date(1950, 3, 15)

    def test_date_from_python_date(self):
        """Test création depuis date Python."""
        py_date = python_date(1950, 3, 15)
        d = Date.from_python_date(py_date)
        assert d.day == 15
        assert d.month == 3
        assert d.year == 1950

    def test_date_incomplete_no_python_conversion(self):
        """Test qu'une date incomplète ne peut pas être convertie."""
        d = Date(year=1950)
        assert d.to_python_date() is None

    def test_date_with_text(self):
        """Test date avec texte libre."""
        d = Date(text="Vers le printemps 1950")
        assert str(d) == "Vers le printemps 1950"


# ============================================================================
# Tests pour Event
# ============================================================================


class TestEvent:
    """Tests pour la classe Event."""

    def test_event_creation(self):
        """Test création d'un événement."""
        event = Event(event_type=EventType.BIRTH, date=Date(day=15, month=3, year=1950), place="Paris, France")
        assert event.event_type == EventType.BIRTH
        assert event.date.year == 1950
        assert event.place == "Paris, France"

    def test_event_string_representation(self):
        """Test représentation textuelle d'un événement."""
        event = Event(event_type=EventType.MARRIAGE, date=Date(year=1975), place="Lyon")
        assert "MARRIAGE" in str(event)
        assert "1975" in str(event)
        assert "Lyon" in str(event)


# ============================================================================
# Tests pour Person
# ============================================================================


class TestPerson:
    """Tests pour la classe Person."""

    def test_person_creation_minimal(self):
        """Test création d'une personne minimale."""
        person = Person(id=1, first_name="John", surname="Doe", sex=Sex.MALE)
        assert person.id == 1
        assert person.first_name == "John"
        assert person.surname == "Doe"
        assert person.sex == Sex.MALE

    def test_person_full_name(self):
        """Test méthode full_name."""
        person = Person(id=1, first_name="John", surname="Doe", sex=Sex.MALE)
        assert person.full_name() == "John Doe"

    def test_person_display_name_without_public_name(self):
        """Test nom d'affichage sans nom public."""
        person = Person(id=1, first_name="John", surname="Doe", sex=Sex.MALE)
        assert person.display_name() == "John Doe"

    def test_person_display_name_with_public_name(self):
        """Test nom d'affichage avec nom public."""
        person = Person(id=1, first_name="John", surname="Doe", sex=Sex.MALE, public_name="Johnny")
        assert person.display_name() == "John 'Johnny' Doe"

    def test_person_with_birth_date(self):
        """Test personne avec date de naissance."""
        person = Person(
            id=1, first_name="John", surname="Doe", sex=Sex.MALE, birth_date=Date(day=15, month=3, year=1950)
        )
        assert person.birth_date.year == 1950
        assert person.birth_date.day == 15

    def test_person_age_at_death(self):
        """Test calcul de l'âge au décès."""
        person = Person(
            id=1, first_name="John", surname="Doe", sex=Sex.MALE, birth_date=Date(year=1950), death_date=Date(year=2020)
        )
        assert person.age_at_death() == 70

    def test_person_age_at_death_incomplete_dates(self):
        """Test calcul d'âge avec dates incomplètes."""
        person = Person(id=1, first_name="John", surname="Doe", sex=Sex.MALE, birth_date=Date(year=1950))
        assert person.age_at_death() is None

    def test_person_is_alive_default(self):
        """Test statut vivant par défaut."""
        person = Person(id=1, first_name="John", surname="Doe", sex=Sex.MALE)
        assert person.is_alive()

    def test_person_is_alive_when_dead(self):
        """Test statut décédé."""
        person = Person(id=1, first_name="John", surname="Doe", sex=Sex.MALE, death_type=DeathType.DEAD)
        assert not person.is_alive()

    def test_person_add_event(self):
        """Test ajout d'événement."""
        person = Person(id=1, first_name="John", surname="Doe", sex=Sex.MALE)
        event = Event(event_type=EventType.OCCUPATION, note="Engineer")

        person.add_event(event)

        assert len(person.events) == 1
        assert person.events[0].event_type == EventType.OCCUPATION

    def test_person_get_events_by_type(self):
        """Test récupération d'événements par type."""
        person = Person(id=1, first_name="John", surname="Doe", sex=Sex.MALE)

        person.add_event(Event(event_type=EventType.BIRTH))
        person.add_event(Event(event_type=EventType.OCCUPATION))
        person.add_event(Event(event_type=EventType.OCCUPATION))

        occupations = person.get_events_by_type(EventType.OCCUPATION)
        assert len(occupations) == 2


# ============================================================================
# Tests pour Family
# ============================================================================


class TestFamily:
    """Tests pour la classe Family."""

    def test_family_creation_minimal(self):
        """Test création d'une famille minimale."""
        family = Family(id=1)
        assert family.id == 1
        assert family.father_id is None
        assert family.mother_id is None

    def test_family_with_parents(self):
        """Test famille avec parents."""
        family = Family(id=1, father_id=10, mother_id=20)
        assert family.has_father()
        assert family.has_mother()
        assert family.father_id == 10
        assert family.mother_id == 20

    def test_family_add_child(self):
        """Test ajout d'enfant."""
        family = Family(id=1)

        family.add_child(100)
        family.add_child(101)

        assert family.has_children()
        assert family.number_of_children() == 2
        assert 100 in family.children_ids
        assert 101 in family.children_ids

    def test_family_add_child_no_duplicate(self):
        """Test qu'un enfant ne peut pas être ajouté deux fois."""
        family = Family(id=1)

        family.add_child(100)
        family.add_child(100)

        assert family.number_of_children() == 1

    def test_family_is_married(self):
        """Test statut marié."""
        family = Family(id=1, marriage_type=MarriageType.MARRIED)
        assert family.is_married()

    def test_family_is_not_married(self):
        """Test statut non marié."""
        family = Family(id=1, marriage_type=MarriageType.NOT_MARRIED)
        assert not family.is_married()

    def test_family_is_divorced(self):
        """Test statut divorcé."""
        family = Family(id=1, divorce_type=DivorceType.DIVORCED)
        assert family.is_divorced()

    def test_family_is_not_divorced(self):
        """Test statut non divorcé."""
        family = Family(id=1, divorce_type=DivorceType.NOT_DIVORCED)
        assert not family.is_divorced()

    def test_family_with_marriage_details(self):
        """Test famille avec détails de mariage."""
        family = Family(id=1, marriage_date=Date(year=1975), marriage_place="Paris", marriage_type=MarriageType.MARRIED)
        assert family.marriage_date.year == 1975
        assert family.marriage_place == "Paris"
        assert family.is_married()


# ============================================================================
# Tests pour Note et Source
# ============================================================================


class TestNote:
    """Tests pour la classe Note."""

    def test_note_creation(self):
        """Test création d'une note."""
        note = Note(id=1, content="Ceci est une note importante", author="John Doe")
        assert note.id == 1
        assert note.content == "Ceci est une note importante"
        assert note.author == "John Doe"


class TestSource:
    """Tests pour la classe Source."""

    def test_source_creation(self):
        """Test création d'une source."""
        source = Source(
            id=1, title="Registre paroissial", author="Église Saint-Pierre", repository="Archives départementales"
        )
        assert source.id == 1
        assert source.title == "Registre paroissial"
        assert source.repository == "Archives départementales"


# ============================================================================
# Tests d'intégration
# ============================================================================


class TestIntegration:
    """Tests d'intégration entre les modèles."""

    def test_complete_person_with_events(self):
        """Test personne complète avec événements."""
        person = Person(
            id=1,
            first_name="Jean",
            surname="Dupont",
            sex=Sex.MALE,
            birth_date=Date(day=15, month=3, year=1950),
            birth_place="Paris, France",
            death_date=Date(year=2020),
            death_type=DeathType.DEAD,
        )

        # Ajouter des événements
        person.add_event(Event(event_type=EventType.OCCUPATION, note="Ingénieur"))
        person.add_event(Event(event_type=EventType.RESIDENCE, place="Lyon", date=Date(year=1975)))

        # Vérifications
        assert person.full_name() == "Jean Dupont"
        assert person.age_at_death() == 70
        assert not person.is_alive()
        assert len(person.events) == 2

    def test_family_with_complete_data(self):
        """Test famille complète avec tous les détails."""
        family = Family(
            id=1,
            father_id=10,
            mother_id=20,
            children_ids=[100, 101, 102],
            marriage_date=Date(day=10, month=6, year=1975),
            marriage_place="Lyon, France",
            marriage_type=MarriageType.MARRIED,
        )

        assert family.has_father()
        assert family.has_mother()
        assert family.has_children()
        assert family.number_of_children() == 3
        assert family.is_married()
        assert not family.is_divorced()
