"""
Core definitions and data structures for GenEWeb

This module contains the fundamental data types used throughout the GenEWeb
system, carefully translated from the original OCaml definitions while
maintaining full compatibility.

Copyright (c) 1998-2007 INRIA
Python modernization preserving original structure and functionality.
"""

from typing import Optional, List, Dict, Union, Any, Tuple
from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime, date


# HTTP Response Status
class HttpStatus(Enum):
    OK = 200
    MOVED_TEMPORARILY = 302
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


class HttpException(Exception):
    """Exception for HTTP status errors"""
    def __init__(self, status: HttpStatus, message: str):
        self.status = status
        self.message = message
        super().__init__(f"{status.name}: {message}")


# Date and Calendar types
class Calendar(Enum):
    GREGORIAN = "gregorian"
    JULIAN = "julian"
    FRENCH = "french"
    HEBREW = "hebrew"


class Precision(Enum):
    SURE = "sure"
    ABOUT = "about"
    MAYBE = "maybe"
    BEFORE = "before"
    AFTER = "after"
    OR_YEAR = "or_year"
    YEAR_INT = "year_int"


@dataclass
class DateMY2:
    """Secondary date for intervals"""
    day2: int
    month2: int
    year2: int
    delta2: int


@dataclass
class DateMY:
    """Date Month Year structure"""
    day: int
    month: int
    year: int
    prec: Precision
    delta: int


@dataclass
class GeneDate:
    """Genealogical date - can be gregorian date or text"""
    # Union type: either structured date or text
    gregorian_date: Optional[Tuple[DateMY, Calendar]] = None
    text_date: Optional[str] = None
    
    @classmethod
    def from_gregorian(cls, dmy: DateMY, calendar: Calendar = Calendar.GREGORIAN):
        return cls(gregorian_date=(dmy, calendar))
    
    @classmethod
    def from_text(cls, text: str):
        return cls(text_date=text)


# Family and relationship types
class RelationKind(Enum):
    MARRIED = "married"
    NOT_MARRIED = "not_married"
    ENGAGED = "engaged"
    NO_SEXES_CHECK_NOT_MARRIED = "no_sexes_check_not_married"
    NO_MENTION = "no_mention"
    NO_SEXES_CHECK_MARRIED = "no_sexes_check_married"
    MARRIAGE_BANN = "marriage_bann"
    MARRIAGE_CONTRACT = "marriage_contract"
    MARRIAGE_LICENSE = "marriage_license"
    PACS = "pacs"
    RESIDENCE = "residence"


class DivorceStatus(Enum):
    NOT_DIVORCED = "not_divorced"
    DIVORCED = "divorced"
    SEPARATED_OLD = "separated_old"
    NOT_SEPARATED = "not_separated"
    SEPARATED = "separated"


@dataclass
class Divorce:
    status: DivorceStatus
    date: Optional[GeneDate] = None


# Death and burial
class DeathReason(Enum):
    KILLED = "killed"
    MURDERED = "murdered"
    EXECUTED = "executed"
    DISAPPEARED = "disappeared"
    UNSPECIFIED = "unspecified"


class DeathStatus(Enum):
    NOT_DEAD = "not_dead"
    DEATH = "death"
    DEAD_YOUNG = "dead_young"
    DEAD_DONT_KNOW_WHEN = "dead_dont_know_when"
    DONT_KNOW_IF_DEAD = "dont_know_if_dead"
    OF_COURSE_DEAD = "of_course_dead"


@dataclass
class Death:
    status: DeathStatus
    reason: Optional[DeathReason] = None
    date: Optional[GeneDate] = None


class BurialType(Enum):
    UNKNOWN_BURIAL = "unknown_burial"
    BURIED = "buried"
    CREMATED = "cremated"


@dataclass
class Burial:
    burial_type: BurialType
    date: Optional[GeneDate] = None


# Access and privacy
class Access(Enum):
    IF_TITLES = "if_titles"
    PUBLIC = "public"
    SEMI_PUBLIC = "semi_public"
    PRIVATE = "private"


# Titles and nobility
class TitleName(Enum):
    MAIN = "main"
    NAME = "name"
    NONE = "none"


@dataclass
class Title:
    """Noble title information"""
    name: Union[TitleName, str]
    identifier: str
    place: str
    date_start: Optional[GeneDate]
    date_end: Optional[GeneDate]
    nth: int


# Events and witnesses
class WitnessKind(Enum):
    WITNESS = "witness"
    WITNESS_GOD_PARENT = "witness_god_parent"
    WITNESS_CIVIL_OFFICER = "witness_civil_officer"
    WITNESS_RELIGIOUS_OFFICER = "witness_religious_officer"
    WITNESS_INFORMANT = "witness_informant"
    WITNESS_ATTENDING = "witness_attending"
    WITNESS_MENTIONED = "witness_mentioned"
    WITNESS_OTHER = "witness_other"


# Personal event types
class PersonalEventName(Enum):
    BIRTH = "birth"
    BAPTISM = "baptism"
    DEATH = "death"
    BURIAL = "burial"
    CREMATION = "cremation"
    ACCOMPLISHMENT = "accomplishment"
    ACQUISITION = "acquisition"
    ADHESION = "adhesion"
    BAPTISM_LDS = "baptism_lds"
    BAR_MITZVAH = "bar_mitzvah"
    BAT_MITZVAH = "bat_mitzvah"
    BENEDICTION = "benediction"
    CHANGE_NAME = "change_name"
    CIRCUMCISION = "circumcision"
    CONFIRMATION = "confirmation"
    CONFIRMATION_LDS = "confirmation_lds"
    DECORATION = "decoration"
    DEMOBILISATION_MILITAIRE = "demobilisation_militaire"
    DIPLOMA = "diploma"
    DISTINCTION = "distinction"
    DOTATION = "dotation"
    DOTATION_LDS = "dotation_lds"
    EDUCATION = "education"
    ELECTION = "election"
    EMIGRATION = "emigration"
    EXCOMMUNICATION = "excommunication"
    FAMILY_LINK_LDS = "family_link_lds"
    FIRST_COMMUNION = "first_communion"
    FUNERAL = "funeral"
    GRADUATE = "graduate"
    HOSPITALISATION = "hospitalisation"
    ILLNESS = "illness"
    IMMIGRATION = "immigration"
    LISTE_PASSENGER = "liste_passenger"
    MILITARY_DISTINCTION = "military_distinction"
    MILITARY_PROMOTION = "military_promotion"
    MILITARY_SERVICE = "military_service"
    MOBILISATION_MILITAIRE = "mobilisation_militaire"
    NATURALISATION = "naturalisation"
    OCCUPATION = "occupation"
    ORDINATION = "ordination"
    PROPERTY = "property"
    RECENSEMENT = "recensement"
    RESIDENCE = "residence"
    RETIRED = "retired"
    SCELLENT_CHILD_LDS = "scellent_child_lds"
    SCELLENT_PARENT_LDS = "scellent_parent_lds"
    SCELLENT_SPOUSE_LDS = "scellent_spouse_lds"
    VENTE_BIEN = "vente_bien"
    WILL = "will"
    CUSTOM = "custom"  # For custom event names


@dataclass
class PersonalEvent:
    """Personal event information"""
    name: Union[PersonalEventName, str]  # Can be enum value or custom string
    date: Optional[GeneDate]
    place: str
    reason: str
    note: str
    source: str
    witnesses: List[Tuple[Any, WitnessKind]]  # Any will be Person type


# Family event types
class FamilyEventName(Enum):
    MARRIAGE = "marriage"
    NO_MARRIAGE = "no_marriage"
    NO_MENTION = "no_mention"
    ENGAGE = "engage"
    DIVORCE = "divorce"
    SEPARATED = "separated"
    ANNULATION = "annulation"
    MARRIAGE_BANN = "marriage_bann"
    MARRIAGE_CONTRACT = "marriage_contract"
    MARRIAGE_LICENSE = "marriage_license"
    PACS = "pacs"
    RESIDENCE = "residence"
    CUSTOM = "custom"  # For custom event names


@dataclass
class FamilyEvent:
    """Family event information"""
    name: Union[FamilyEventName, str]  # Can be enum value or custom string
    date: Optional[GeneDate]
    place: str
    reason: str
    note: str
    source: str
    witnesses: List[Tuple[Any, WitnessKind]]  # Any will be Person type


# Relations and adoption
class RelationType(Enum):
    ADOPTION = "adoption"
    RECOGNITION = "recognition"
    CANDIDATE_PARENT = "candidate_parent"
    GOD_PARENT = "god_parent"
    FOSTER_PARENT = "foster_parent"


@dataclass
class Relation:
    """Relation information with parents (if not native)"""
    relation_type: RelationType
    father: Optional[Any]  # Will be Person type
    mother: Optional[Any]  # Will be Person type
    sources: str


# Sex
class Sex(Enum):
    MALE = "male"
    FEMALE = "female"
    NEUTER = "neuter"


# Place information
@dataclass
class Place:
    """Geographic place information"""
    other: str = ""
    town: str = ""
    township: str = ""
    canton: str = ""
    district: str = ""
    county: str = ""
    region: str = ""
    country: str = ""


# Core person structure
@dataclass
class Person:
    """Core person information structure"""
    # Names and identification
    first_name: str
    surname: str
    occurrence: int  # For distinguishing homonyms
    
    # Additional names and aliases
    public_name: str = ""
    qualifiers: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    first_names_aliases: List[str] = field(default_factory=list)
    surnames_aliases: List[str] = field(default_factory=list)
    
    # Titles and relations
    titles: List[Title] = field(default_factory=list)
    relations_with_parents: List[Relation] = field(default_factory=list)
    related_persons: List[Any] = field(default_factory=list)  # List of Person references
    
    # Basic info
    occupation: str = ""
    sex: Sex = Sex.NEUTER
    access: Access = Access.PRIVATE
    image: str = ""
    
    # Birth information
    birth_date: Optional[GeneDate] = None
    birth_place: str = ""
    birth_note: str = ""
    birth_source: str = ""
    
    # Baptism information
    baptism_date: Optional[GeneDate] = None
    baptism_place: str = ""
    baptism_note: str = ""
    baptism_source: str = ""
    
    # Death information
    death: Optional[Death] = None
    death_place: str = ""
    death_note: str = ""
    death_source: str = ""
    
    # Burial information
    burial: Optional[Burial] = None
    burial_place: str = ""
    burial_note: str = ""
    burial_source: str = ""
    
    # Events and notes
    personal_events: List[PersonalEvent] = field(default_factory=list)
    notes: str = ""
    sources: str = ""
    
    # System fields
    key_index: Optional[Any] = None  # Will be database key type


@dataclass
class Ascendants:
    """Person's ascendants (family where they are children)"""
    parents_family: Optional[Any] = None  # Will be Family type
    consanguinity: float = 0.0  # Relationship between parents


@dataclass
class Union:
    """Person's families where they are parent"""
    families: List[Any] = field(default_factory=list)  # List of Family references


@dataclass
class Descendants:
    """Children of a family"""
    children: List[Any] = field(default_factory=list)  # List of Person references


@dataclass
class Couple:
    """Couple in a family"""
    father: Optional[Any] = None  # Person reference
    mother: Optional[Any] = None  # Person reference


@dataclass
class Family:
    """Family information structure"""
    # Marriage information
    marriage_date: Optional[GeneDate] = None
    marriage_place: str = ""
    marriage_note: str = ""
    marriage_source: str = ""
    witnesses: List[Any] = field(default_factory=list)  # List of Person references
    
    # Relationship
    relation: RelationKind = RelationKind.MARRIED
    divorce: Optional[Divorce] = None
    
    # Events and sources
    family_events: List[FamilyEvent] = field(default_factory=list)
    comment: str = ""
    origin_file: str = ""  # .gw filename where family is defined
    sources: str = ""
    
    # System fields
    family_index: Optional[Any] = None  # Will be database key type


# Database errors and warnings
class PersonError(Exception):
    """Database errors describing bad specification of person"""
    pass


class AlreadyDefinedError(PersonError):
    def __init__(self, person):
        self.person = person
        super().__init__(f"Person already defined: {person}")


class OwnAncestorError(PersonError):
    def __init__(self, person):
        self.person = person
        super().__init__(f"Person is their own ancestor: {person}")


class BadSexOfMarriedPersonError(PersonError):
    def __init__(self, person):
        self.person = person
        super().__init__(f"Bad sex of married person: {person}")


# Warning types (for data validation)
class WarningType(Enum):
    BIG_AGE_BETWEEN_SPOUSES = "big_age_between_spouses"
    BIRTH_AFTER_DEATH = "birth_after_death"
    INCOHERENT_SEX = "incoherent_sex"
    CHANGED_ORDER_OF_CHILDREN = "changed_order_of_children"
    CHANGED_ORDER_OF_MARRIAGES = "changed_order_of_marriages"
    CHANGED_ORDER_OF_FAMILY_EVENTS = "changed_order_of_family_events"
    CHANGED_ORDER_OF_PERSON_EVENTS = "changed_order_of_person_events"
    CHILDREN_NOT_IN_ORDER = "children_not_in_order"
    CLOSE_CHILDREN = "close_children"
    DEAD_OLD = "dead_old"
    DEAD_TOO_EARLY_TO_BE_FATHER = "dead_too_early_to_be_father"
    DISTANT_CHILDREN = "distant_children"
    FEVENT_ORDER = "fevent_order"
    FWITNESS_EVENT_AFTER_DEATH = "fwitness_event_after_death"
    FWITNESS_EVENT_BEFORE_BIRTH = "fwitness_event_before_birth"
    INCOHERENT_ANCESTOR_DATE = "incoherent_ancestor_date"
    MARRIAGE_DATE_AFTER_DEATH = "marriage_date_after_death"
    MARRIAGE_DATE_BEFORE_BIRTH = "marriage_date_before_birth"
    MOTHER_DEAD_BEFORE_CHILD_BIRTH = "mother_dead_before_child_birth"
    PARENT_BORN_AFTER_CHILD = "parent_born_after_child"
    PARENT_TOO_OLD = "parent_too_old"
    PARENT_TOO_YOUNG = "parent_too_young"
    PEVENT_ORDER = "pevent_order"
    POSSIBLE_DUPLICATE_FAM = "possible_duplicate_fam"
    POSSIBLE_DUPLICATE_FAM_HOMONYMOUS = "possible_duplicate_fam_homonymous"
    PWITNESS_EVENT_AFTER_DEATH = "pwitness_event_after_death"
    PWITNESS_EVENT_BEFORE_BIRTH = "pwitness_event_before_birth"
    TITLE_DATES_ERROR = "title_dates_error"
    UNDEFINED_SEX = "undefined_sex"
    YOUNG_FOR_MARRIAGE = "young_for_marriage"
    OLD_FOR_MARRIAGE = "old_for_marriage"
    MISSING_SOURCES = "missing_sources"


@dataclass
class Warning:
    """Database warning"""
    warning_type: WarningType
    details: Dict[str, Any] = field(default_factory=dict)


# Database note reading modes
class ReadingMode(Enum):
    ALL = "all"          # Read all content
    FIRST_LINE = "1ln"   # Read first line
    DEGREE = "deg"       # If file isn't empty returns a space


@dataclass
class BaseNotes:
    """Database note/page explorer structure"""
    # These will be implemented as methods in the actual database class
    pass


# Update modifications for history tracking
class UpdateType(Enum):
    ADD_PERSON = "add_person"
    MODIFY_PERSON = "modify_person"
    DELETE_PERSON = "delete_person"
    MERGE_PERSON = "merge_person"
    SEND_IMAGE = "send_image"
    DELETE_IMAGE = "delete_image"
    ADD_FAMILY = "add_family"
    MODIFY_FAMILY = "modify_family"
    DELETE_FAMILY = "delete_family"
    INVERT_FAMILY = "invert_family"
    MERGE_FAMILY = "merge_family"
    CHANGE_CHILDREN_NAME = "change_children_name"
    ADD_PARENT = "add_parent"
    KILL_ANCESTORS = "kill_ancestors"
    MULTI = "multi"
    NOTES = "notes"


@dataclass
class BaseUpdate:
    """Database update for history tracking"""
    update_type: UpdateType
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


# Name linking database (NLDB) types
class PageType(Enum):
    INDIVIDUAL = "individual"
    FAMILY = "family"
    NOTES = "notes"
    MISC = "misc"
    WIZARD = "wizard"


@dataclass
class NameKey:
    """Key for name lookup"""
    first_name: str
    surname: str
    occurrence: int
    
    def __eq__(self, other):
        if not isinstance(other, NameKey):
            return False
        return (self.occurrence == other.occurrence and 
                self.first_name == other.first_name and 
                self.surname == other.surname)
    
    def __hash__(self):
        return hash((self.first_name, self.surname, self.occurrence))


@dataclass
class NameIndex:
    """Index entry for name lookup"""
    text: Optional[str] = None
    position: int = 0


# Utility functions for string operations
def concat_with_sep(sep: str, *parts: str) -> str:
    """Concatenate strings with separator, equivalent to OCaml ^^^"""
    return sep.join(filter(None, parts))


def concat_space(*parts: str) -> str:
    """Concatenate strings with space separator, equivalent to OCaml ^>^"""
    return concat_with_sep(" ", *parts)


def concat_comma(*parts: str) -> str:
    """Concatenate strings with comma separator, equivalent to OCaml ^<^"""
    return concat_with_sep(", ", *parts)
