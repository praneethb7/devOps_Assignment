import pytest

from app.fares import FareError, base_fare, quote, total


def test_base_fare_is_distance_times_rate():
    assert base_fare(100) == 275.0


@pytest.mark.parametrize("bad", [0, -1, -0.5])
def test_base_fare_rejects_non_positive_distance(bad):
    with pytest.raises(FareError):
        base_fare(bad)


def test_class_multiplier_applies():
    assert quote(100, "economy") == 275.0
    assert quote(100, "premium") == 440.0
    assert quote(100, "business") == 687.5


def test_travel_class_is_case_insensitive():
    assert quote(100, "BUSINESS") == quote(100, "business")


def test_unknown_class_is_rejected():
    with pytest.raises(FareError):
        quote(100, "first")


def test_peak_surcharge():
    assert quote(100, "economy", peak=True) == 385.0


def test_child_discount_halves_the_fare():
    assert quote(100, "economy", child=True) == 137.5


def test_total_multiplies_by_passengers():
    assert total(100, 3, travel_class="economy") == 825.0


def test_total_rejects_zero_passengers():
    with pytest.raises(FareError):
        total(100, 0)
