"""Fare rules for the yatri booking service.

Pure functions, no I/O - which is what makes them cheap to unit test
in CI without a database or a network.
"""

BASE_FARE_PER_KM = 2.75
PEAK_MULTIPLIER = 1.4
CLASS_MULTIPLIER = {"economy": 1.0, "premium": 1.6, "business": 2.5}
CHILD_DISCOUNT = 0.5


class FareError(ValueError):
    """Raised when a fare cannot be calculated from the inputs given."""


def base_fare(distance_km: float) -> float:
    if distance_km <= 0:
        raise FareError("distance_km must be positive")
    return round(distance_km * BASE_FARE_PER_KM, 2)


def quote(distance_km: float, travel_class: str = "economy",
          peak: bool = False, child: bool = False) -> float:
    """Full fare for one passenger."""
    travel_class = travel_class.lower()
    if travel_class not in CLASS_MULTIPLIER:
        raise FareError(f"unknown travel class: {travel_class}")

    fare = base_fare(distance_km) * CLASS_MULTIPLIER[travel_class]
    if peak:
        fare *= PEAK_MULTIPLIER
    if child:
        fare *= CHILD_DISCOUNT
    return round(fare, 2)


def total(distance_km: float, passengers: int, **kwargs) -> float:
    if passengers < 1:
        raise FareError("passengers must be at least 1")
    return round(quote(distance_km, **kwargs) * passengers, 2)
