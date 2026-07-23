"""Pytest configuration: shared fixtures for the test suite."""

import pytest

from services.models import ServiceCenter

TEST_CITIES = ("تهران", "مشهد", "Tehran")


@pytest.fixture
def ensure_test_cities(db):
    """Create ServiceCenter records for cities used in tests.

    RegisterForm and ProfileForm validate that the submitted city exists
    in the ServiceCenter table via ``clean_city()``.  Without matching
    records the form is always invalid, causing cascading test failures.
    """
    for city_name in TEST_CITIES:
        ServiceCenter.objects.get_or_create(
            name=f"مرکز {city_name}",
            defaults={"city": city_name},
        )
