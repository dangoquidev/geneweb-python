"""
Security and authentication module for GenEWeb

This module handles all security aspects including authentication,
authorization, password management, and access control.
Translated from the original OCaml authentication and security modules.

Copyright (c) 1998-2007 INRIA
Python modernization preserving original structure and functionality.
"""

import base64
import hashlib
import hmac
import logging
import os
import secrets
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from ..core.config import Config
from ..core.definitions import Access


class AccessLevel(Enum):
    """Access levels for users"""

    VISITOR = "visitor"
    FRIEND = "friend"
    WIZARD = "wizard"
    MANITOU = "manitou"
    SUPERVISOR = "supervisor"


@dataclass
class AuthUser:
    """Authenticated user information"""

    username: str
    password_hash: str
    info: str = ""
    access_level: AccessLevel = AccessLevel.VISITOR


@dataclass
class AuthResult:
    """Result of authentication attempt"""

    success: bool
    user: Optional[AuthUser] = None
    error_message: str = ""
    can_retry: bool = True
    requires_digest_auth: bool = False


class SecurityManager:
    """
    Main security manager handling authentication and authorization
    """

    def __init__(self, config: Config):
        self.config = config
        self.auth_users: Dict[str, AuthUser] = {}
        self.active_sessions: Dict[str, Tuple[str, float]] = {}  # token -> (username, timestamp)
        self.failed_attempts: Dict[str, List[float]] = {}  # IP -> timestamps
        self.secret_key = self._get_or_create_secret_key()

        # Load authentication files
        self._load_auth_files()

    def _get_or_create_secret_key(self) -> str:
        """Get or create secret key for session management"""
        if self.config.secret_salt:
            return self.config.secret_salt

        # Try to load from file
        key_file = os.path.join(self.config.database_name, "secret.key")
        if os.path.exists(key_file):
            try:
                with open(key_file, "r") as f:
                    return f.read().strip()
            except Exception:
                pass

        # Generate new key
        key = secrets.token_hex(32)

        # Try to save it
        try:
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, "w") as f:
                f.write(key)
        except Exception:
            pass

        return key

    def _load_auth_files(self) -> None:
        """Load authentication files (wizard_passwd_file, friend_passwd_file)"""
        # Load wizard users
        wizard_file = self._get_auth_file_path("wizard_passwd_file")
        if wizard_file:
            self._load_auth_file(wizard_file, AccessLevel.WIZARD)

        # Load friend users
        friend_file = self._get_auth_file_path("friend_passwd_file")
        if friend_file:
            self._load_auth_file(friend_file, AccessLevel.FRIEND)

    def _get_auth_file_path(self, file_key: str) -> Optional[str]:
        """Get authentication file path from configuration"""
        for key, value in self.config.base_environment:
            if key == file_key and value:
                if os.path.isabs(value):
                    return value
                else:
                    return os.path.join(self.config.database_name, value)
        return None

    def _load_auth_file(self, file_path: str, default_access: AccessLevel) -> None:
        """Load users from authentication file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        self._parse_auth_line(line, default_access)
        except Exception as e:
            logging.warning(f"Failed to load auth file {file_path}: {e}")

    def _parse_auth_line(self, line: str, default_access: AccessLevel) -> None:
        """Parse a line from authentication file"""
        # Format: username:password or username:password:info
        parts = line.split(":")
        if len(parts) >= 2:
            username = parts[0].strip()
            password = parts[1].strip()
            info = parts[2].strip() if len(parts) > 2 else ""

            # Create auth user
            auth_user = AuthUser(
                username=username,
                password_hash=self._hash_password(password),
                info=info,
                access_level=default_access,
            )

            self.auth_users[username] = auth_user

    def _hash_password(self, password: str) -> str:
        """Hash a password using a secure method"""
        # Use PBKDF2 with SHA256
        salt = hashlib.sha256(password.encode()).digest()[:16]
        return base64.b64encode(hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)).decode()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return self._hash_password(password) == password_hash

    def _check_rate_limiting(self, ip_address: str) -> bool:
        """Check if IP address is rate limited"""
        current_time = time.time()
        max_attempts = 5
        time_window = 300  # 5 minutes

        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = []

        # Remove old attempts outside time window
        attempts = self.failed_attempts[ip_address]
        self.failed_attempts[ip_address] = [attempt for attempt in attempts if current_time - attempt < time_window]

        return len(self.failed_attempts[ip_address]) < max_attempts

    def _record_failed_attempt(self, ip_address: str) -> None:
        """Record a failed authentication attempt"""
        current_time = time.time()
        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = []

        self.failed_attempts[ip_address].append(current_time)

    def authenticate_basic(self, username: str, password: str, ip_address: str) -> AuthResult:
        """Authenticate using basic authentication"""
        # Check rate limiting
        if not self._check_rate_limiting(ip_address):
            return AuthResult(
                success=False,
                error_message="Too many failed attempts. Please try again later.",
                can_retry=False,
            )

        # Check if user exists
        if username not in self.auth_users:
            self._record_failed_attempt(ip_address)
            return AuthResult(
                success=False,
                error_message="Invalid username or password",
                can_retry=True,
            )

        user = self.auth_users[username]

        # Verify password
        if not self._verify_password(password, user.password_hash):
            self._record_failed_attempt(ip_address)
            return AuthResult(
                success=False,
                error_message="Invalid username or password",
                can_retry=True,
            )

        return AuthResult(success=True, user=user)

    def authenticate_digest(self, auth_header: str, method: str, uri: str, ip_address: str) -> AuthResult:
        """Authenticate using digest authentication"""
        # Parse digest auth header
        digest_params = self._parse_digest_auth_header(auth_header)
        if not digest_params:
            return AuthResult(
                success=False,
                error_message="Invalid digest authentication header",
            )

        username = digest_params.get("username", "")
        realm = digest_params.get("realm", "")
        nonce = digest_params.get("nonce", "")
        uri_param = digest_params.get("uri", "")
        response = digest_params.get("response", "")

        # Check if user exists
        if username not in self.auth_users:
            return AuthResult(success=False, error_message="Invalid username")

        user = self.auth_users[username]

        # Verify digest response
        if self._verify_digest_response(
            username,
            realm,
            method,
            uri_param,
            nonce,
            response,
            user.password_hash,
        ):
            return AuthResult(success=True, user=user)
        else:
            self._record_failed_attempt(ip_address)
            return AuthResult(success=False, error_message="Invalid digest response")

    def _parse_digest_auth_header(self, auth_header: str) -> Dict[str, str]:
        """Parse digest authentication header"""
        if not auth_header.startswith("Digest "):
            return {}

        params: dict[str, str] = {}
        content = auth_header[7:]  # Remove 'Digest '

        # Simple parsing - in production, use a proper parser
        pairs = content.split(",")
        for pair in pairs:
            pair = pair.strip()
            if "=" in pair:
                key, value = pair.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"')
                params[key] = value

        return params

    def _verify_digest_response(
        self,
        username: str,
        realm: str,
        method: str,
        uri: str,
        nonce: str,
        response: str,
        password_hash: str,
    ) -> bool:
        """Verify digest authentication response"""
        # This is a simplified implementation
        # In production, you'd need proper digest auth implementation

        # For now, just check if response matches expected format
        ha1 = hashlib.md5(f"{username}:{realm}:{password_hash}".encode()).hexdigest()
        ha2 = hashlib.md5(f"{method}:{uri}".encode()).hexdigest()
        expected_response = hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()

        return response == expected_response

    def create_session_token(self, username: str) -> str:
        """Create a session token for user"""
        timestamp = str(int(time.time()))
        data = f"{username}:{timestamp}"
        signature = hmac.new(self.secret_key.encode(), data.encode(), hashlib.sha256).hexdigest()

        token = base64.b64encode(f"{data}:{signature}".encode()).decode()

        # Store in active sessions
        self.active_sessions[token] = (username, time.time())

        return token

    def verify_session_token(self, token: str) -> Optional[str]:
        """Verify session token and return username"""
        try:
            decoded = base64.b64decode(token.encode()).decode()
            parts = decoded.split(":")
            if len(parts) != 3:
                return None

            username, timestamp, signature = parts

            # Verify signature
            data = f"{username}:{timestamp}"
            expected_signature = hmac.new(self.secret_key.encode(), data.encode(), hashlib.sha256).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                return None

            # Check if token exists in active sessions
            if token in self.active_sessions:
                stored_username, _ = self.active_sessions[token]
                if stored_username == username:
                    return username

            return None

        except Exception:
            return None

    def revoke_session_token(self, token: str) -> bool:
        """Revoke a session token"""
        if token in self.active_sessions:
            del self.active_sessions[token]
            return True
        return False

    def cleanup_expired_sessions(self, max_age: int = 3600) -> None:
        """Clean up expired session tokens"""
        current_time = time.time()
        expired_tokens: list[str] = []

        for token, (username, timestamp) in self.active_sessions.items():
            if current_time - timestamp > max_age:
                expired_tokens.append(token)

        for token in expired_tokens:
            del self.active_sessions[token]

    def check_access_permission(self, user_access: AccessLevel, required_access: AccessLevel) -> bool:
        """Check if user has required access level"""
        access_hierarchy = {
            AccessLevel.VISITOR: 0,
            AccessLevel.FRIEND: 1,
            AccessLevel.WIZARD: 2,
            AccessLevel.MANITOU: 3,
            AccessLevel.SUPERVISOR: 4,
        }

        return access_hierarchy.get(user_access, 0) >= access_hierarchy.get(required_access, 0)

    def can_access_person(
        self,
        user_access: AccessLevel,
        person_access: Access,
        has_titles: bool = False,
        has_dates: bool = True,
    ) -> bool:
        """Check if user can access person with given access level"""
        # Public persons are always accessible
        if person_access == Access.PUBLIC:
            return True

        # Check user access level
        if user_access in [
            AccessLevel.WIZARD,
            AccessLevel.MANITOU,
            AccessLevel.SUPERVISOR,
        ]:
            return True

        if user_access == AccessLevel.FRIEND:
            return person_access in [Access.PUBLIC, Access.SEMI_PUBLIC]

        # Visitor access - check special conditions
        if person_access == Access.SEMI_PUBLIC and self.config.semi_public:
            return True

        if person_access == Access.IF_TITLES and self.config.public_if_titles and has_titles:
            return True

        if not has_dates and self.config.public_if_no_date:
            return True

        return False

    def generate_nonce(self) -> str:
        """Generate nonce for digest authentication"""
        return secrets.token_hex(16)

    def create_digest_challenge(self, realm: str) -> str:
        """Create digest authentication challenge"""
        nonce = self.generate_nonce()
        return f'Digest realm="{realm}", nonce="{nonce}", qop="auth"'

    def hash_password_for_storage(self, password: str) -> str:
        """Hash password for secure storage"""
        return self._hash_password(password)

    def add_user(
        self,
        username: str,
        password: str,
        access_level: AccessLevel,
        info: str = "",
    ) -> bool:
        """Add a new user"""
        if username in self.auth_users:
            return False

        auth_user = AuthUser(
            username=username,
            password_hash=self._hash_password(password),
            info=info,
            access_level=access_level,
        )

        self.auth_users[username] = auth_user
        return True

    def remove_user(self, username: str) -> bool:
        """Remove a user"""
        if username in self.auth_users:
            del self.auth_users[username]

            # Remove any active sessions for this user
            tokens_to_remove: list[str] = []
            for token, (stored_username, _) in self.active_sessions.items():
                if stored_username == username:
                    tokens_to_remove.append(token)

            for token in tokens_to_remove:
                del self.active_sessions[token]

            return True
        return False

    def change_user_password(self, username: str, new_password: str) -> bool:
        """Change user password"""
        if username in self.auth_users:
            self.auth_users[username].password_hash = self._hash_password(new_password)
            return True
        return False

    def get_user_info(self, username: str) -> Optional[AuthUser]:
        """Get user information"""
        return self.auth_users.get(username)

    def list_users(self) -> List[str]:
        """List all usernames"""
        return list(self.auth_users.keys())


def create_security_manager(config: Config) -> SecurityManager:
    """Factory function to create security manager"""
    return SecurityManager(config)


def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """Validate password strength and return (is_valid, error_messages)"""
    errors: list[str] = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")

    return (len(errors) == 0, errors)


def secure_compare(a: str, b: str) -> bool:
    """Secure string comparison to prevent timing attacks"""
    return hmac.compare_digest(a, b)


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)
