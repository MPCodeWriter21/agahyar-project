"""Map-related utilities for service center location data.

Provides city center coordinate lookup and prepares serializable
data for Leaflet map rendering on the frontend.
"""

CITY_COORDINATES: dict[str, tuple[float, float]] = {
    "تهران": (35.6892, 51.3890),
    "مشهد": (36.2605, 59.6168),
    "اصفهان": (32.6546, 51.6680),
    "شیراز": (29.5926, 52.5836),
    "تبریز": (38.0802, 46.2919),
    "کرج": (35.8327, 50.9915),
    "قم": (34.6399, 50.8759),
    "اهواز": (31.3183, 48.6706),
    "رشت": (37.2809, 49.5832),
    "کرمانشاه": (34.3082, 47.0573),
    "زاهدان": (29.4963, 60.8629),
    "ارومیه": (37.5553, 45.0799),
}


def get_city_center(city: str) -> dict[str, float]:
    """Return the central map coordinates for *city*.

    Falls back to Tehran if the city is not in the lookup table.

    :param city: Persian city name (e.g. ``"تهران"``).
    :returns: A dict with ``"lat"`` and ``"lng"`` keys.
    """
    lat, lng = CITY_COORDINATES.get(city, (35.6892, 51.3890))
    return {"lat": lat, "lng": lng}


def get_center_locations(centers) -> list[dict]:
    """Return serializable location data for a QuerySet of ServiceCenters.

    Only includes centers that have a non-null ``coordinate``.

    :param centers: QuerySet of :class:`ServiceCenter` instances.
    :returns: List of dicts with ``lat``, ``lng``, ``name``,
        ``address``, ``phone`` keys.
    """
    locations = []
    for c in centers:
        if c.coordinate is not None:
            locations.append(
                {
                    "lat": c.coordinate.y,
                    "lng": c.coordinate.x,
                    "name": c.name,
                    "address": c.address or "",
                    "phone": c.phone or "",
                }
            )
    return locations
