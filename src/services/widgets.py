"""Custom admin widgets for the Agahyar services application.

Provides ``LocalOpenLayersWidget`` with Neshan search and manual
coordinate input for the admin map widget, and ``TagListWidget``
for editing pipe/comma-separated lists with add/remove/reorder.
"""

import html as html_module
import re

from django import forms
from django.contrib.gis.forms.widgets import OpenLayersWidget
from django.forms.widgets import Media
from django.utils.safestring import mark_safe


class LocalOpenLayersWidget(OpenLayersWidget):
    """OpenLayersWidget that uses local files and OSM tiles.

    Overrides the default CDN-based Media so the admin map widget
    respects the project's Content-Security-Policy.
    Switches from NASA BlueMarble to OpenStreetMap tiles for the same reason.

    Adds a Neshan search box and lat/lng coordinate input fields around
    the map widget, loaded from the project's static files.
    """

    base_layer = "osm"

    @property
    def media(self):
        """Return Media with local vendored OpenLayers paths only."""
        return Media(
            css={"all": ["libs/ol/ol.css", "gis/css/ol3.css"]},
            js=[
                "libs/ol/ol.js",
                "gis/js/OLMapWidget.js",
                "services/js/admin-map-widget.js",
            ],
        )

    def render(self, name, value, attrs=None, renderer=None):
        """Render the map widget with Neshan search and coordinate inputs."""
        html = super().render(name, value, attrs, renderer)

        # Extract the field id from the rendered HTML reliably
        m = re.search(r'id="([^"]+)_div_map"', html)
        if not m:
            return mark_safe(html)  # nosec B308 B703
        field_id = m.group(1)

        # Add neshan-widget-wrapper class to the existing wrapper div
        html = html.replace(
            f'id="{field_id}_div_map" class="dj_map_wrapper"',
            f'id="{field_id}_div_map" class="dj_map_wrapper neshan-widget-wrapper"',
        )

        search_box = (
            f'<div class="neshan-search-container">'
            f'<input type="text" id="{field_id}_search" '
            f'class="neshan-search-input" '
            f'placeholder="\u062c\u0633\u062a\u062c\u0648\u06cc \u0645\u06a9\u0627\u0646..." '
            f'autocomplete="off" dir="rtl" />'
            f'<button type="button" id="{field_id}_search_btn" '
            f'class="neshan-search-btn" '
            f'title="\u062c\u0633\u062a\u062c\u0648">\u062c\u0633\u062a\u062c\u0648</button>'
            f'<div id="{field_id}_search_results" '
            f'class="neshan-search-results"></div>'
            f"</div>"
        )

        coord_inputs = (
            f'<div class="neshan-coord-inputs">'
            f'<div class="neshan-coord-field">'
            f'<label for="{field_id}_lat_input">Latitude</label>'
            f'<input type="number" id="{field_id}_lat_input" '
            f'class="neshan-lat-input neshan-coord-field-input" '
            f'step="any" min="-90" max="90" '
            f'placeholder="35.6892" dir="ltr" />'
            f"</div>"
            f'<div class="neshan-coord-field">'
            f'<label for="{field_id}_lng_input">Longitude</label>'
            f'<input type="number" id="{field_id}_lng_input" '
            f'class="neshan-lng-input neshan-coord-field-input" '
            f'step="any" min="-180" max="180" '
            f'placeholder="51.3890" dir="ltr" />'
            f"</div>"
            f"</div>"
        )

        # Insert search box right before the map div
        map_div_marker = f'<div id="{field_id}_map"'
        html = html.replace(map_div_marker, search_box + "\n    " + map_div_marker)

        # Insert coord inputs before the textarea (the hidden serialized field)
        textarea_marker = f'<textarea id="{field_id}"'
        html = html.replace(textarea_marker, coord_inputs + "\n    " + textarea_marker)

        return mark_safe(html)  # nosec B308 B703


class TagListWidget(forms.Widget):
    """Widget for editing a separator-delimited list of items.

    Renders each item as a separate input field with drag-and-drop
    reordering, add, and remove buttons.  The hidden input holds the
    serialized (separator-joined) value.

    Args:
        separator: The character used to join/split items (default ``"|"``).
        attrs: Extra HTML attributes for the widget wrapper.
    """

    template_name = "admin/taglist_widget.html"

    def __init__(self, separator="|", attrs=None):
        self.separator = separator
        super().__init__(attrs=attrs)

    @property
    def media(self):
        return Media(
            css={"all": ["services/css/admin-rtl.css"]},
            js=["services/js/admin-taglist-widget.js"],
        )

    def value_from_datadict(self, data, files, name):
        return data.get(name, "")

    def value_omitted_from_data(self, data, files, name):
        return name not in data

    def render(self, name, value, attrs=None, renderer=None):
        value = value or ""
        widget_id = attrs.get("id", f"id_{name}") if attrs else f"id_{name}"
        items = value.split(self.separator) if value else []

        html_parts = [
            f'<div class="tag-list-widget" id="{widget_id}_taglist"'
            f' data-separator="{self.separator}">'
            f'<input type="hidden" name="{name}" id="{widget_id}"'
            f' value="{html_module.escape(value)}">'
            f'<div class="tag-list-items">'
        ]

        for item in items:
            escaped = html_module.escape(item.strip())
            html_parts.append(
                f'<div class="tag-list-item">'
                f'<span class="tag-list-drag-handle" title="Drag to reorder">&#x2630;</span>'
                f'<input type="text" class="tag-list-input" value="{escaped}">'
                f'<button type="button" class="tag-list-remove-btn" title="Remove">&times;</button>'
                f"</div>"
            )

        html_parts.append("</div>")
        html_parts.append(
            '<button type="button" class="tag-list-add-btn">+ Add</button>'
        )
        html_parts.append("</div>")

        return mark_safe("\n".join(html_parts))  # nosec B308 B703
