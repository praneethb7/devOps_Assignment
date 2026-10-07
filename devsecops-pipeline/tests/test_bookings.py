import pytest

from app.bookings import BookingError, sign_reference, validate_reference, verify_reference


@pytest.fixture(autouse=True)
def signing_key(monkeypatch):
    monkeypatch.setenv("BOOKING_SIGNING_KEY", "test-key-not-a-real-secret")


def test_valid_reference_passes():
    assert validate_reference("YT-ABC123") == "YT-ABC123"


@pytest.mark.parametrize("bad", ["", "YT-abc123", "XX-ABC123", "YT-ABC12", None])
def test_malformed_references_rejected(bad):
    with pytest.raises(BookingError):
        validate_reference(bad)


def test_signature_is_stable():
    assert sign_reference("YT-ABC123") == sign_reference("YT-ABC123")


def test_signature_differs_per_reference():
    assert sign_reference("YT-ABC123") != sign_reference("YT-ABC124")


def test_verify_accepts_its_own_signature():
    assert verify_reference("YT-ABC123", sign_reference("YT-ABC123"))


def test_verify_rejects_a_wrong_signature():
    assert not verify_reference("YT-ABC123", "0" * 64)


def test_missing_key_is_an_error(monkeypatch):
    monkeypatch.delenv("BOOKING_SIGNING_KEY")
    with pytest.raises(BookingError):
        sign_reference("YT-ABC123")
