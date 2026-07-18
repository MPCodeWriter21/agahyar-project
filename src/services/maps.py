"""Map-related utilities for service center location data.

Provides city center coordinate lookup and prepares serializable
data for Leaflet map rendering on the frontend.
"""


def get_city_center(city: str) -> dict[str, float]:
    """Return the central map coordinates for *city*.

    Computes the average latitude and longitude of all ServiceCenters
    in the given city that have coordinates.  Falls back to Tehran
    coordinates if no matching centers are found.

    :param city: Persian city name (e.g. ``"تهران"``).
    :returns: A dict with ``"lat"`` and ``"lng"`` keys.
    """
    from .models import ServiceCenter

    centers = list(
        ServiceCenter.objects.filter(
            city__icontains=city, coordinate__isnull=False
        ).values_list("coordinate", flat=True)
    )
    if centers:
        avg_lat = sum(c.y for c in centers) / len(centers)
        avg_lng = sum(c.x for c in centers) / len(centers)
        return {"lat": avg_lat, "lng": avg_lng}
    return {"lat": 35.6892, "lng": 51.3890}


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
