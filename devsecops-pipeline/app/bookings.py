"""Booking reference handling for the yatri service."""
import hashlib
import hmac
import os
import re

REFERENCE_RE = re.compile(r"^YT-[A-Z0-9]{6}$")


class BookingError(ValueError):
    """Raised for invalid booking input."""


def _signing_key() -> bytes:
    """Read the signing key from the environment.

    Deliberately not defaulted to a literal: a hardcoded fallback is exactly
    what the secret scanning stage of the pipeline is meant to catch.
    """
    key = os.environ.get("BOOKING_SIGNING_KEY")
    if not key:
        raise BookingError("BOOKING_SIGNING_KEY is not set")
    return key.encode()


def validate_reference(reference: str) -> str:
    if not REFERENCE_RE.match(reference or ""):
        raise BookingError(f"malformed booking reference: {reference!r}")
    return reference


def sign_reference(reference: str) -> str:
    """HMAC-SHA256 over the reference.

    SHA256 and hmac rather than md5/sha1 - a SAST scanner flags the weak
    hashes, and it is right to.
    """
    validate_reference(reference)
    return hmac.new(_signing_key(), reference.encode(), hashlib.sha256).hexdigest()


def verify_reference(reference: str, signature: str) -> bool:
    """Constant-time comparison; `==` here would leak timing information."""
    return hmac.compare_digest(sign_reference(reference), signature)
