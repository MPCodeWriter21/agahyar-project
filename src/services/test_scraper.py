import pytest

from services.scraper import get_ai_suggestion, get_nearest_center


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
class TestGetAiSuggestion:
    def test_returns_fallback_when_no_centers_exist(self):
        result = get_ai_suggestion("گواهینامه رانندگی", "تهران")
        assert isinstance(result, list)
        assert len(result) >= 2
        assert result[0]["name"] == "دفتر پیشخوان تهران"
        assert result[0]["phone"] == "---"
        assert result[1]["name"] == "اداره گواهینامه رانندگی در تهران"

    def test_exception_logged_gracefully(self):
        result = get_ai_suggestion("", "")
        assert isinstance(result, list)
        assert len(result) >= 2

    def test_fallback_uses_nearest_centers_when_db_empty(self):
        result = get_ai_suggestion("صدور کارت ملی هوشمند", "تهران")
        assert isinstance(result, list)
        assert len(result) >= 1
        assert "ثبت احوال تهران" in result[0]["name"]

    def test_fallback_prefers_nearest_centers_over_placeholder(self):
        result = get_ai_suggestion("صدور پاسپورت", "تهران")
        assert isinstance(result, list)
        assert result[0]["name"] != "دفتر پیشخوان تهران"
