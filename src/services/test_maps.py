"""Tests for the maps module.

Verifies city center coordinate lookup and service center
location serialization.
"""

import pytest
from django.contrib.gis.geos import Point
from django.test import Client

from services.maps import CITY_COORDINATES, get_center_locations, get_city_center
from services.models import Service, ServiceCenter, User


class TestGetCityCenter:
    def test_returns_tehran_coords(self):
        center = get_city_center("تهران")
        assert center == {"lat": 35.6892, "lng": 51.3890}

    def test_returns_shiraz_coords(self):
        center = get_city_center("شیراز")
        assert center == {"lat": 29.5926, "lng": 52.5836}

    def test_falls_back_to_tehran_for_unknown_city(self):
        center = get_city_center("نامشخص")
        assert center == {"lat": 35.6892, "lng": 51.3890}

    def test_all_cities_have_valid_coordinates(self):
        for city, (lat, lng) in CITY_COORDINATES.items():
            assert -90 <= lat <= 90, f"{city} lat out of range"
            assert -180 <= lng <= 180, f"{city} lng out of range"


@pytest.mark.django_db
class TestGetCenterLocations:
    def test_returns_empty_list_for_no_centers(self):
        assert get_center_locations([]) == []

    def test_serializes_center_with_coordinate(self):
        svc = Service.objects.create(
            name="test", organization="o", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=svc,
            name="مرکز الف",
            address="آدرس یک",
            city="تهران",
            phone="02112345678",
            coordinate=Point(51.3890, 35.6892, srid=4326),
        )
        result = get_center_locations([center])
        assert len(result) == 1
        assert result[0]["lat"] == 35.6892
        assert result[0]["lng"] == 51.3890
        assert result[0]["name"] == "مرکز الف"
        assert result[0]["address"] == "آدرس یک"
        assert result[0]["phone"] == "02112345678"

    def test_skips_center_without_coordinate(self):
        svc = Service.objects.create(
            name="test", organization="o", documents="d", steps="s"
        )
        center = ServiceCenter.objects.create(
            service=svc,
            name="بدون مختصات",
            address="آدرس",
            city="تهران",
        )
        result = get_center_locations([center])
        assert result == []

    def test_handles_mixed_centers(self):
        svc = Service.objects.create(
            name="test", organization="o", documents="d", steps="s"
        )
        with_coord = ServiceCenter.objects.create(
            service=svc,
            name="دارد",
            address="آدرس",
            city="تهران",
            coordinate=Point(51.3890, 35.6892, srid=4326),
        )
        without_coord = ServiceCenter.objects.create(
            service=svc,
            name="ندارد",
            address="آدرس",
            city="تهران",
        )
        result = get_center_locations([with_coord, without_coord])
        assert len(result) == 1
        assert result[0]["name"] == "دارد"


@pytest.mark.django_db
class TestServiceDetailMapContext:
    def test_center_locations_in_context(self):
        User.objects.create_user("mapuser", password="pass12345")
        svc = Service.objects.create(
            name="map-svc", organization="org", documents="d", steps="s"
        )
        ServiceCenter.objects.create(
            service=svc,
            name="مرکز الف",
            address="آدرس",
            city="تهران",
            coordinate=Point(51.3890, 35.6892, srid=4326),
        )
        ServiceCenter.objects.create(
            service=svc,
            name="مرکز ب",
            address="آدرس ۲",
            city="تهران",
            coordinate=Point(51.4000, 35.7000, srid=4326),
        )
        client = Client()
        client.login(username="mapuser", password="pass12345")
        response = client.get(f"/service/{svc.id}/")
        assert "center_locations" in response.context
        locations = response.context["center_locations"]
        assert len(locations) == 2

    def test_center_locations_empty_when_no_centers(self):
        User.objects.create_user("mapuser2", password="pass12345")
        svc = Service.objects.create(
            name="map-svc2", organization="org", documents="d", steps="s"
        )
        client = Client()
        client.login(username="mapuser2", password="pass12345")
        response = client.get(f"/service/{svc.id}/")
        assert "center_locations" in response.context
        assert response.context["center_locations"] == []

    def test_city_center_in_context(self):
        User.objects.create_user("mapuser3", password="pass12345")
        svc = Service.objects.create(
            name="map-svc3", organization="org", documents="d", steps="s"
        )
        client = Client()
        client.login(username="mapuser3", password="pass12345")
        response = client.get(f"/service/{svc.id}/")
        assert "city_center" in response.context
        assert "lat" in response.context["city_center"]
        assert "lng" in response.context["city_center"]
