"""
Configuration management for GenEWeb

This module handles all configuration aspects of the GenEWeb system,
including authentication, web server settings, database configuration,
and user preferences. Translated from the original OCaml config.ml.

Copyright (c) 1998-2007 INRIA
Python modernization preserving original structure and functionality.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from .definitions import Access, DateMY, HttpStatus, Precision, Sex


# Authentication scheme types
class AuthSchemeKind(Enum):
    NO_AUTH = "no_auth"
    TOKEN_AUTH = "token_auth"
    HTTP_AUTH = "http_auth"


@dataclass
class TokenAuthScheme:
    user: str
    password: str


class HttpAuthType(Enum):
    BASIC = "basic"
    DIGEST = "digest"


@dataclass
class BasicAuthScheme:
    realm: str
    user: str
    password: str


@dataclass
class DigestAuthScheme:
    username: str
    realm: str
    nonce: str
    method: str
    uri: str
    qop: str
    nc: str
    cnonce: str
    response: str


@dataclass
class HttpAuthScheme:
    auth_type: HttpAuthType
    basic: Optional[BasicAuthScheme] = None
    digest: Optional[DigestAuthScheme] = None


@dataclass
class AuthScheme:
    kind: AuthSchemeKind
    token_auth: Optional[TokenAuthScheme] = None
    http_auth: Optional[HttpAuthScheme] = None


# Output configuration for HTTP responses
@dataclass
class OutputConfig:
    """Configuration for HTTP output handling"""

    status_handler: Callable[[HttpStatus], None]
    header_handler: Callable[[str], None]
    body_handler: Callable[[str], None]
    flush_handler: Callable[[], None]


# Environment type (query parameters and form data)
Environment = List[Tuple[str, str]]


@dataclass
class Config:
    """
    Main configuration class for GenEWeb
    Contains all settings and state needed for operation
    """

    # Connection and request info
    from_address: str = ""
    api_mode: bool = False
    manitou: bool = False  # Special admin privileges
    supervisor: bool = False  # Supervisor privileges
    wizard: bool = False  # Full access privileges
    is_printed_by_template: bool = False
    debug: bool = False
    query_start_time: float = 0.0
    friend: bool = False  # Friend access level
    semi_public: bool = False
    just_friend_wizard: bool = False  # Wizard restricted to friend access

    # User information
    user: str = ""
    username: str = ""
    userkey: str = ""
    user_id: Optional[Any] = None  # Will be database ID type
    auth_scheme: AuthScheme = field(default_factory=lambda: AuthScheme(AuthSchemeKind.NO_AUTH))

    # Command and request
    command: str = ""
    independent_command: str = ""
    highlight: str = ""

    # Language and localization
    language: str = ""
    vowels: List[str] = field(default_factory=list)
    default_language: str = ""
    browser_language: str = ""
    default_sosa_reference: Tuple[Optional[Any], Optional[Any]] = (
        None,
        None,
    )  # (ID, Person)

    # Database and family options
    multi_parents: bool = False
    authorized_wizards_notes: bool = False
    public_if_titles: bool = False
    public_if_no_date: bool = False
    setup_link: bool = False
    access_by_key: bool = False

    # Privacy settings
    private_years: int = 150
    private_years_death: int = 150
    private_years_marriage: int = 150
    hide_names: bool = False
    use_restrict: bool = False
    no_image: bool = False
    no_note: bool = False

    # Database info
    database_name: str = ""
    number_of_persons: int = 0
    number_of_families: int = 0
    cgi_password: str = ""

    # Environment variables
    environment: Environment = field(default_factory=list)
    session_environment: Environment = field(default_factory=list)
    hidden_environment: Environment = field(default_factory=list)
    base_environment: List[Tuple[str, str]] = field(default_factory=list)  # Content of .gwf file

    # Access control
    allowed_titles: List[str] = field(default_factory=list)
    denied_titles: List[str] = field(default_factory=list)

    # Request data
    request_lines: List[str] = field(default_factory=list)
    lexicon: Dict[str, str] = field(default_factory=dict)

    # Display settings
    charset: str = "UTF-8"
    is_right_to_left: bool = False
    left_direction: str = "left"
    right_direction: str = "right"
    auth_file: str = ""
    border: int = 0

    # Connection tracking
    connection_info: Optional[Tuple[int, int, int, List[Tuple[str, float]]]] = None

    # Date and time
    today: DateMY = field(default_factory=lambda: DateMY(day=0, month=0, year=0, prec=Precision.SURE, delta=0))
    today_weekday: int = 0
    current_time: Tuple[int, int, int] = (0, 0, 0)  # (hour, minute, second)
    current_timestamp: float = 0.0

    # Web server settings
    geneweb_prefix: str = ""
    images_prefix: str = ""
    etc_prefix: str = ""
    cgi_mode: bool = False

    # Output configuration
    output_config: Optional[OutputConfig] = None

    # Plugin system
    forced_plugins: List[str] = field(default_factory=list)
    plugins: List[str] = field(default_factory=list)
    secret_salt: Optional[str] = None
    predictable_mode: bool = False

    @classmethod
    def create_empty(cls) -> "Config":
        """Create an empty configuration for testing purposes"""
        return cls()

    def is_authenticated_user(self) -> bool:
        """Check if current user is authenticated"""
        return self.wizard or self.friend

    def has_full_access(self) -> bool:
        """Check if user has full database access"""
        return self.wizard and not self.just_friend_wizard

    def can_edit(self) -> bool:
        """Check if user can edit database"""
        return self.wizard and not self.just_friend_wizard

    def can_view_private(self) -> bool:
        """Check if user can view private information"""
        return self.wizard or self.friend

    def get_environment_value(self, key: str, default: str = "") -> str:
        """Get value from environment variables"""
        for k, v in self.environment:
            if k == key:
                return v
        return default

    def get_lexicon_translation(self, key: str, default: str = "") -> str:
        """Get translation from lexicon"""
        return self.lexicon.get(key, default)

    def is_person_accessible(
        self,
        access_level: Access,
        has_titles: bool = False,
        has_dates: bool = True,
    ) -> bool:
        """
        Determine if a person with given access level is accessible to current user
        """
        if self.can_view_private():
            return True

        if access_level == Access.PUBLIC:
            return True

        if access_level == Access.SEMI_PUBLIC and self.semi_public:
            return True

        if access_level == Access.IF_TITLES and self.public_if_titles and has_titles:
            return True

        if not has_dates and self.public_if_no_date:
            return True

        return False

    def get_effective_language(self) -> str:
        """Get the effective language to use"""
        if self.language:
            return self.language
        if self.browser_language:
            return self.browser_language
        return self.default_language

    def get_display_direction(self) -> Tuple[str, str]:
        """Get left/right direction strings based on RTL setting"""
        if self.is_right_to_left:
            return ("right", "left")
        return ("left", "right")

    def update_timestamp(self) -> None:
        """Update current timestamp and related time fields"""
        now = datetime.now()
        self.current_timestamp = now.timestamp()
        self.current_time = (now.hour, now.minute, now.second)
        self.today = DateMY(
            day=now.day,
            month=now.month,
            year=now.year,
            prec=Precision.SURE,
            delta=0,
        )
        self.today_weekday = now.weekday()

    def get_request_url(self) -> str:
        """Reconstruct the request URL"""
        # This would be implemented based on the web framework being used
        return f"/{self.database_name}"

    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        if not self.database_name:
            errors.append("Database name is required")

        if self.private_years < 0:
            errors.append("Private years must be non-negative")

        if not self.default_language:
            errors.append("Default language is required")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization"""
        # Implementation would serialize all fields to a dict
        # This is useful for debugging and logging
        return {
            "database_name": self.database_name,
            "user": self.user,
            "wizard": self.wizard,
            "friend": self.friend,
            "language": self.language,
            "private_years": self.private_years,
            # ... add other important fields
        }

    def __str__(self) -> str:
        """String representation for debugging"""
        return f"Config(db='{self.database_name}', user='{self.user}', wizard={self.wizard}, friend={self.friend})"


def create_default_output_config() -> OutputConfig:
    """Create default output configuration"""

    def default_status(status: HttpStatus) -> None:
        pass

    def default_header(header: str) -> None:
        pass

    def default_body(body: str) -> None:
        pass

    def default_flush() -> None:
        pass

    return OutputConfig(
        status_handler=default_status,
        header_handler=default_header,
        body_handler=default_body,
        flush_handler=default_flush,
    )


def read_base_environment(base_file: str, gw_prefix: str, debug: bool = False) -> List[Tuple[str, str]]:
    """
    Read base environment from .gwf file
    This function reads configuration from the base's .gwf file
    """
    base_env = []
    gwf_file = base_file + ".gwf"

    try:
        with open(gwf_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        base_env.append((key.strip(), value.strip()))
    except FileNotFoundError:
        if debug:
            print(f"Warning: Base environment file {gwf_file} not found")
    except Exception as e:
        if debug:
            print(f"Error reading base environment file {gwf_file}: {e}")

    return base_env


def alias_language(lang: str) -> str:
    """
    Get language alias from alias configuration
    Maps language codes to their canonical forms
    """
    if len(lang) < 2:
        return lang

    # Try to read language aliases file
    try:
        with open("lang/alias_lg.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    alias, canonical = line.split("=", 1)
                    if lang == alias.strip():
                        return canonical.strip()
    except FileNotFoundError:
        pass

    return lang


def get_vowels_for_language(base_env: List[Tuple[str, str]]) -> List[str]:
    """Get vowels list for the configured language"""
    for key, value in base_env:
        if key == "vowels":
            # Parse vowels from string - this would need proper UTF-8 handling
            vowels = []
            i = 0
            while i < len(value):
                # Simple implementation - in real version would need proper UTF-8 parsing
                vowels.append(value[i])
                i += 1
            return vowels

    # Default vowels
    return ["a", "e", "i", "o", "u", "y"]
