"""
Utility functions for GenEWeb

This module contains various utility functions used throughout the system,
including string manipulation, date handling, file operations, and more.
Translated from multiple OCaml utility modules.

Copyright (c) 1998-2007 INRIA
Python modernization preserving original structure and functionality.
"""

import base64
import hashlib
import os
import re
import shutil
import tempfile
import unicodedata
from datetime import date, datetime
from typing import List, Optional, Tuple, Union
from urllib.parse import quote, unquote

from ..core.definitions import Calendar, DateMY, GeneDate, Precision


def normalize_name(name: str) -> str:
    """
    Normalize a name for comparison and sorting
    Removes accents, converts to lowercase, handles special characters
    """
    if not name:
        return ""

    # Remove accents and normalize Unicode
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")

    # Convert to lowercase
    name = name.lower()

    # Replace special characters with spaces for better matching
    name = re.sub(r"['\-_.,;:!?]", " ", name)  # Replace punctuation with spaces
    name = re.sub(r"[^\w\s]", "", name)  # Remove remaining special chars
    name = re.sub(r"\s+", " ", name)  # Normalize whitespace

    return name.strip()


def compare_names(name1: str, name2: str) -> bool:
    """Compare two names for equality after normalization"""
    return normalize_name(name1) == normalize_name(name2)


def encode_string(s: str) -> str:
    """URL encode a string"""
    return quote(s, safe="")


def decode_string(s: str) -> str:
    """URL decode a string"""
    return unquote(s)


def create_environment(query_string: str) -> List[Tuple[str, str]]:
    """
    Parse query string into environment list
    Similar to OCaml's create_env function
    """
    if not query_string:
        return []

    env: list[str] = []
    pairs = query_string.split("&")

    for pair in pairs:
        if "=" in pair:
            key, value = pair.split("=", 1)
            env.append((decode_string(key), decode_string(value)))
        elif pair:
            env.append((decode_string(pair), ""))

    return env


def get_environment_value(env: List[Tuple[str, str]], key: str) -> Optional[str]:
    """Get value from environment list"""
    for k, v in env:
        if k == key:
            return v
    return None


def get_environment_int(env: List[Tuple[str, str]], key: str) -> Optional[int]:
    """Get integer value from environment list"""
    value = get_environment_value(env, key)
    if value:
        try:
            return int(value)
        except ValueError:
            pass
    return None


def extract_parameter(param_name: str, separator: str, text: str) -> str:
    """
    Extract a parameter from text (like HTTP headers)
    Similar to OCaml's extract_param function
    """
    if not text:
        return ""

    lines = text.split("\n")
    for line in lines:
        if line.lower().startswith(param_name.lower()):
            rest = line[len(param_name) :].strip()
            if separator in rest:
                return rest.split(separator)[0].strip()
            return rest

    return ""


def starts_with(prefix: str, start_pos: int, text: str) -> bool:
    """Check if text starts with prefix at given position"""
    if start_pos + len(prefix) > len(text):
        return False
    return text[start_pos : start_pos + len(prefix)] == prefix


def ends_with(suffix: str, text: str) -> bool:
    """Check if text ends with suffix"""
    return text.endswith(suffix)


def remove_extension(filename: str) -> str:
    """Remove file extension from filename"""
    return os.path.splitext(filename)[0]


def get_extension(filename: str) -> str:
    """Get file extension"""
    return os.path.splitext(filename)[1]


def secure_filename(filename: str) -> str:
    """Make a filename safe for use"""
    # Remove path separators and other dangerous characters
    filename = re.sub(r'[/\\:*?"<>|]', "_", filename)
    # Remove leading/trailing dots and spaces
    filename = filename.strip(". ")
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[: 255 - len(ext)] + ext

    return filename


def make_directory(path: str) -> bool:
    """Create directory if it doesn't exist"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError:
        return False


def copy_file(src: str, dest: str) -> bool:
    """Copy file from src to dest"""
    try:
        shutil.copy2(src, dest)
        return True
    except (OSError, IOError):
        return False


def move_file(src: str, dest: str) -> bool:
    """Move file from src to dest"""
    try:
        shutil.move(src, dest)
        return True
    except (OSError, IOError):
        return False


def file_exists(path: str) -> bool:
    """Check if file exists"""
    return os.path.isfile(path)


def directory_exists(path: str) -> bool:
    """Check if directory exists"""
    return os.path.isdir(path)


def get_file_size(path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def get_file_modified_time(path: str) -> Optional[datetime]:
    """Get file modification time"""
    try:
        timestamp = os.path.getmtime(path)
        return datetime.fromtimestamp(timestamp)
    except OSError:
        return None


def read_file_lines(path: str, encoding: str = "utf-8") -> List[str]:
    """Read all lines from a file"""
    try:
        with open(path, "r", encoding=encoding) as f:
            return f.readlines()
    except (OSError, IOError, UnicodeDecodeError):
        return []


def write_file_lines(path: str, lines: List[str], encoding: str = "utf-8") -> bool:
    """Write lines to a file"""
    try:
        with open(path, "w", encoding=encoding) as f:
            f.writelines(lines)
        return True
    except (OSError, IOError, UnicodeEncodeError):
        return False


def create_temporary_file(suffix: str = "", prefix: str = "geneweb_") -> Optional[str]:
    """Create a temporary file and return its path"""
    try:
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
        os.close(fd)  # Close the file descriptor, keep the file
        return path
    except OSError:
        return None


def create_temporary_directory(suffix: str = "", prefix: str = "geneweb_") -> Optional[str]:
    """Create a temporary directory and return its path"""
    try:
        return tempfile.mkdtemp(suffix=suffix, prefix=prefix)
    except OSError:
        return None


def cleanup_temporary_file(path: str) -> bool:
    """Remove a temporary file"""
    try:
        os.remove(path)
        return True
    except OSError:
        return False


def cleanup_temporary_directory(path: str) -> bool:
    """Remove a temporary directory and its contents"""
    try:
        shutil.rmtree(path)
        return True
    except OSError:
        return False


def calculate_md5(text: str) -> str:
    """Calculate MD5 hash of text"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def calculate_file_md5(path: str) -> Optional[str]:
    """Calculate MD5 hash of file"""
    try:
        hash_md5 = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except (OSError, IOError):
        return None


def base64_encode(data: bytes) -> str:
    """Base64 encode data"""
    return base64.b64encode(data).decode("ascii")


def base64_decode(encoded: str) -> bytes:
    """Base64 decode string"""
    return base64.b64decode(encoded.encode("ascii"))


def generate_random_string(length: int = 8) -> str:
    """Generate a random string"""
    import random
    import string

    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def format_date_string(date_obj: Union[datetime, date]) -> str:
    """Format date as string"""
    if isinstance(date_obj, datetime):
        return date_obj.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return date_obj.strftime("%Y-%m-%d")


def parse_date_string(date_str: str) -> Optional[datetime]:
    """Parse date string into datetime object"""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def date_to_geneweb_date(date_obj: Union[datetime, date], precision: Precision = Precision.SURE) -> GeneDate:
    """Convert Python date to GenEWeb date"""
    if isinstance(date_obj, datetime):
        dmy = DateMY(
            day=date_obj.day,
            month=date_obj.month,
            year=date_obj.year,
            prec=precision,
            delta=0,
        )
    else:
        dmy = DateMY(
            day=date_obj.day,
            month=date_obj.month,
            year=date_obj.year,
            prec=precision,
            delta=0,
        )

    return GeneDate.from_gregorian(dmy, Calendar.GREGORIAN)


def geneweb_date_to_string(gw_date: GeneDate) -> str:
    """Convert GenEWeb date to string representation"""
    if gw_date.text_date:
        return gw_date.text_date

    if gw_date.gregorian_date:
        dmy, calendar = gw_date.gregorian_date

        # Format the date
        date_str = ""

        if dmy.prec == Precision.ABOUT:
            date_str += "ca "
        elif dmy.prec == Precision.BEFORE:
            date_str += "< "
        elif dmy.prec == Precision.AFTER:
            date_str += "> "
        elif dmy.prec == Precision.MAYBE:
            date_str += "? "

        # Add day if present
        if dmy.day > 0:
            date_str += f"{dmy.day}/"

        # Add month if present
        if dmy.month > 0:
            date_str += f"{dmy.month}/"

        # Add year
        date_str += str(dmy.year)

        # Add calendar notation if not Gregorian
        if calendar == Calendar.JULIAN:
            date_str += " (Julian)"
        elif calendar == Calendar.FRENCH:
            date_str += " (French)"
        elif calendar == Calendar.HEBREW:
            date_str += " (Hebrew)"

        return date_str

    return ""


def is_leap_year(year: int) -> bool:
    """Check if year is a leap year"""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def days_in_month(month: int, year: int) -> int:
    """Get number of days in a month"""
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    elif month in [4, 6, 9, 11]:
        return 30
    elif month == 2:
        return 29 if is_leap_year(year) else 28
    else:
        return 0


def validate_date(day: int, month: int, year: int) -> bool:
    """Validate if date is valid"""
    if year < 1 or month < 1 or month > 12 or day < 1:
        return False

    max_day = days_in_month(month, year)
    return day <= max_day


def calculate_age(birth_date: GeneDate, reference_date: Optional[GeneDate] = None) -> Optional[int]:
    """Calculate age from birth date to reference date (or today)"""
    if not birth_date.gregorian_date:
        return None

    birth_dmy, _ = birth_date.gregorian_date

    if reference_date and reference_date.gregorian_date:
        ref_dmy, _ = reference_date.gregorian_date
    else:
        # Use today's date
        today = datetime.now()
        ref_dmy = DateMY(today.day, today.month, today.year, Precision.SURE, 0)

    # Calculate age
    age = ref_dmy.year - birth_dmy.year

    # Adjust if birthday hasn't occurred this year
    if ref_dmy.month < birth_dmy.month or (ref_dmy.month == birth_dmy.month and ref_dmy.day < birth_dmy.day):
        age -= 1

    return max(0, age)


def escape_html(text: str) -> str:
    """Escape HTML special characters"""
    if not text:
        return ""

    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#39;")

    return text


def unescape_html(text: str) -> str:
    """Unescape HTML special characters"""
    if not text:
        return ""

    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")

    return text


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to maximum length with optional suffix"""
    if len(text) <= max_length:
        return text

    if len(suffix) >= max_length:
        return text[:max_length]

    return text[: max_length - len(suffix)] + suffix


def pluralize(word: str, count: int, plural_form: Optional[str] = None) -> str:
    """Return singular or plural form based on count"""
    if count == 1:
        return word

    if plural_form:
        return plural_form

    # Simple English pluralization rules
    if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
        return word[:-1] + "ies"
    elif word.endswith(("s", "sh", "ch", "x", "z")):
        return word + "es"
    else:
        return word + "s"


def format_number_with_separators(number: int, separator: str = ",") -> str:
    """Format number with thousands separators"""
    return f"{number:,}".replace(",", separator)


def strip_quotes(text: str) -> str:
    """Remove surrounding quotes from text"""
    if len(text) >= 2:
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            return text[1:-1]
    return text


def split_name_parts(full_name: str) -> Tuple[str, str]:
    """
    Split full name into first name and surname
    Handles various name formats
    """
    if not full_name:
        return ("", "")

    full_name = full_name.strip()

    # Handle "surname, first name" format
    if "," in full_name:
        parts = full_name.split(",", 1)
        return (parts[1].strip(), parts[0].strip())

    # Handle "first name surname" format
    parts = full_name.split()
    if len(parts) == 1:
        return (parts[0], "")
    elif len(parts) == 2:
        return (parts[0], parts[1])
    else:
        # Multiple parts - first word is first name, rest is surname
        return (parts[0], " ".join(parts[1:]))


def join_name_parts(first_name: str, surname: str) -> str:
    """Join first name and surname into full name"""
    parts: list[str] = []
    if first_name:
        parts.append(first_name)
    if surname:
        parts.append(surname)
    return " ".join(parts)


class StringBuffer:
    """
    String buffer for efficient string building
    Similar to OCaml's Buffer module
    """

    def __init__(self):
        self.parts = []
        self.length = 0

    def add(self, text: str) -> None:
        """Add text to buffer"""
        self.parts.append(text)
        self.length += len(text)

    def add_char(self, char: str) -> None:
        """Add single character to buffer"""
        self.parts.append(char)
        self.length += 1

    def get_contents(self) -> str:
        """Get buffer contents as string"""
        return "".join(self.parts)

    def clear(self) -> None:
        """Clear buffer"""
        self.parts = []
        self.length = 0

    def get_length(self) -> int:
        """Get current length of buffer"""
        return self.length
