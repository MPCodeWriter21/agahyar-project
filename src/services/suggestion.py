"""Placeholder logic for nearest-center lookup and ranking.

Functions are marked as TODO and currently return simple DB
queries or hardcoded fallback data. See Tigo tasks for the
full implementation.
"""

from __future__ import annotations

from typing import Optional

from log21 import get_logger

from .models import ServiceCenter

logger = get_logger()


def get_nearest_center(
    service_name: str, city: str, neighborhood: str
) -> Optional["ServiceCenter"]:
    """TO BE IMPLEMENTED: Find the nearest service center based on location.

    Currently downgraded: always returns None (views fall back to a simple
    DB query filtered by city). See Tigo task for implementation.

    :param service_name: Name of the requested service.
    :param city: User's city.
    :param neighborhood: User's neighborhood.
    :returns: A :class:`~services.models.ServiceCenter` instance, or None.
    """
    if not service_name or not city or not neighborhood:
        return None

    # TODO: Implement real proximity-based nearest center lookup
    return None


def scrape_passport_info() -> dict:
    """TO BE IMPLEMENTED: Scrape passport information from external sources.

    Currently downgraded: returns hardcoded fallback data.
    See Tigo task for implementation.

    :returns: A dict with ``source`` and ``info`` keys.
    """
    # TODO: Implement real scraping from official sources
    return {
        "source": "دیتابیس داخلی",
        "info": "هزینه پاسپورت عادی ۱۵۰,۰۰۰ تومان و فوری ۳۰۰,۰۰۰ تومان است.",
    }


def suggest_centers(service_name: str, user_city: str) -> list:
    """TO BE IMPLEMENTED: Suggest service centers with smart ranking.

    Currently downgraded: queries DB directly and falls back to generic
    placeholders. No ranking involved yet.
    See Tigo task for implementation.

    :param service_name: Name of the requested service.
    :param user_city: User's city.
    :returns: A list of suggestion dicts with ``name``, ``address``, ``phone``,
        and ``distance`` keys.
    """
    try:
        centers = ServiceCenter.objects.filter(
            service__name__icontains=service_name, city__icontains=user_city
        )[:3]
        if centers.exists():
            return [
                {
                    "name": c.name,
                    "address": c.address,
                    "phone": c.phones.first().phone if c.phones.exists() else "---",
                    "distance": "نزدیک",
                }
                for c in centers
            ]
    except Exception as e:
        logger.error(
            f"Error getting center suggestions for '{service_name}' in '{user_city}': {e}"
        )

    return [
        {
            "name": f"دفتر پیشخوان {user_city}",
            "address": f"خیابان اصلی - {user_city}",
            "phone": "---",
            "distance": "نزدیک",
        },
        {
            "name": f"اداره {service_name} در {user_city}",
            "address": f"میدان مرکزی - {user_city}",
            "phone": "---",
            "distance": "متوسط",
        },
    ]
