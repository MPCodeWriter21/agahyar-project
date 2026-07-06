"""Custom admin widgets for geometry fields with locally vendored OpenLayers."""

from django.contrib.gis.forms.widgets import OpenLayersWidget
from django.forms.widgets import Media


class LocalOpenLayersWidget(OpenLayersWidget):
    """OpenLayersWidget that uses local files and OSM tiles.

    Overrides the default CDN-based Media so the admin map widget
    respects the project's Content-Security-Policy.
    Switches from NASA BlueMarble to OpenStreetMap tiles for the same reason.
    """

    base_layer = "osm"

    @property
    def media(self):
        """Return Media with local vendored OpenLayers paths only."""
        return Media(
            css={"all": ["libs/ol/ol.css", "gis/css/ol3.css"]},
            js=["libs/ol/ol.js", "gis/js/OLMapWidget.js"],
        )
