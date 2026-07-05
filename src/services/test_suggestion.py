import pytest

from services.suggestion import get_nearest_center, suggest_centers


@pytest.mark.django_db
class TestGetNearestCenter:
    def test_returns_none_for_empty_inputs(self):
        assert get_nearest_center(None, "tehran", "saadatabad") is None
        assert get_nearest_center("service", None, "saadatabad") is None
        assert get_nearest_center("service", "tehran", None) is None
        assert get_nearest_center("", "tehran", "") is None

    def test_returns_none_for_missing_neighborhood(self):
        assert get_nearest_center("any", "tehran", "gharb") is None

    def test_returns_none_for_missing_city(self):
        assert get_nearest_center("any", "mashhad", "markazi") is None


@pytest.mark.django_db
class TestSuggestCenters:
    def test_returns_fallback_when_no_centers_exist(self):
        result = suggest_centers("گواهینامه رانندگی", "تهران")
        assert isinstance(result, list)
        assert len(result) >= 2
        assert result[0]["name"] == "دفتر پیشخوان تهران"
        assert result[0]["phone"] == "---"
        assert result[1]["name"] == "اداره گواهینامه رانندگی در تهران"

    def test_exception_logged_gracefully(self):
        result = suggest_centers("", "")
        assert isinstance(result, list)
        assert len(result) >= 2

    def test_placeholder_returned_when_db_empty(self):
        result = suggest_centers("صدور کارت ملی هوشمند", "تهران")
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["name"] == "دفتر پیشخوان تهران"

    def test_placeholder_returned_when_no_match(self):
        result = suggest_centers("صدور پاسپورت", "تهران")
        assert isinstance(result, list)
        assert result[0]["name"] == "دفتر پیشخوان تهران"
