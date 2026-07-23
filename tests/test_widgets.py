"""Tests for the custom admin widgets (OpenLayers map and tag list)."""

import pytest
from django.test import Client

from services.widgets import LocalOpenLayersWidget, TagListWidget


class TestLocalOpenLayersWidget:
    """Verify the widget uses OSM tiles and local vendored files."""

    def test_base_layer_is_osm(self):
        w = LocalOpenLayersWidget()
        assert w.base_layer == "osm"

    def test_media_has_no_cdn_urls(self):
        w = LocalOpenLayersWidget()
        media = w.media
        all_urls = " ".join(media._css.get("all", [])) + " " + " ".join(media._js)
        assert "cdn.jsdelivr.net" not in all_urls

    def test_media_includes_local_ol_files(self):
        w = LocalOpenLayersWidget()
        media = w.media
        css_all = media._css.get("all", [])
        assert "libs/ol/ol.css" in css_all
        assert "gis/css/ol3.css" in css_all
        assert "libs/ol/ol.js" in media._js
        assert "gis/js/OLMapWidget.js" in media._js

    def test_media_includes_admin_map_widget_js(self):
        w = LocalOpenLayersWidget()
        media = w.media
        assert "services/js/admin-map-widget.js" in media._js

    def test_media_includes_no_duplicates(self):
        w = LocalOpenLayersWidget()
        media = w.media
        css_all = media._css.get("all", [])
        assert len(css_all) == len(set(css_all))
        assert len(media._js) == len(set(media._js))

    def test_render_does_not_contain_cdn(self):
        w = LocalOpenLayersWidget()
        html = w.render("coordinate", None, {"id": "id_coordinate"})
        assert "cdn.jsdelivr.net" not in html

    def test_render_contains_search_box(self):
        w = LocalOpenLayersWidget()
        html = w.render("coordinate", None, {"id": "id_coordinate"})
        assert "neshan-search-input" in html
        assert "neshan-search-results" in html

    def test_render_contains_coord_inputs(self):
        w = LocalOpenLayersWidget()
        html = w.render("coordinate", None, {"id": "id_coordinate"})
        assert "neshan-lat-input" in html
        assert "neshan-lng-input" in html
        assert "Latitude" in html
        assert "Longitude" in html

    def test_render_has_search_input_id(self):
        w = LocalOpenLayersWidget()
        html = w.render("coordinate", None, {"id": "id_coordinate"})
        assert 'id="id_coordinate_search"' in html

    def test_render_has_coord_input_ids(self):
        w = LocalOpenLayersWidget()
        html = w.render("coordinate", None, {"id": "id_coordinate"})
        assert 'id="id_coordinate_lat_input"' in html
        assert 'id="id_coordinate_lng_input"' in html

    def test_render_uses_custom_template(self):
        w = LocalOpenLayersWidget()
        assert w.template_name == "gis/openlayers.html"


@pytest.mark.django_db
class TestServiceCenterAdminMapWidget:
    """Verify the ServiceCenter admin page includes the map widget."""

    def test_admin_add_page_renders(self):
        from django.contrib.auth.models import User

        User.objects.create_superuser("admin", "admin@test.com", "admin12345")
        client = Client()
        assert client.login(username="admin", password="admin12345")
        response = client.get("/admin/services/servicecenter/add/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "dj_map" in content

    def test_admin_change_page_renders(self):
        from django.contrib.auth.models import User

        from services.models import Service

        User.objects.create_superuser("admin2", "admin2@test.com", "admin12345")
        svc = Service.objects.create(
            name="admin-map-svc",
            organization="org",
            documents="d",
            steps="s",
        )
        client = Client()
        assert client.login(username="admin2", password="admin12345")
        response = client.get(f"/admin/services/servicecenter/add/?service={svc.id}")
        assert response.status_code == 200
        content = response.content.decode()
        assert "dj_map" in content

    def test_admin_add_page_has_no_cdn(self):
        from django.contrib.auth.models import User

        User.objects.create_superuser("admin3", "admin3@test.com", "admin12345")
        client = Client()
        assert client.login(username="admin3", password="admin12345")
        response = client.get("/admin/services/servicecenter/add/")
        content = response.content.decode()
        assert "cdn.jsdelivr.net" not in content

    def test_admin_add_page_has_search_box(self):
        from django.contrib.auth.models import User

        User.objects.create_superuser("admin4", "admin4@test.com", "admin12345")
        client = Client()
        assert client.login(username="admin4", password="admin12345")
        response = client.get("/admin/services/servicecenter/add/")
        content = response.content.decode()
        assert "neshan-search-input" in content

    def test_admin_add_page_has_coord_inputs(self):
        from django.contrib.auth.models import User

        User.objects.create_superuser("admin5", "admin5@test.com", "admin12345")
        client = Client()
        assert client.login(username="admin5", password="admin12345")
        response = client.get("/admin/services/servicecenter/add/")
        content = response.content.decode()
        assert "neshan-lat-input" in content
        assert "neshan-lng-input" in content

    def test_admin_add_page_has_phone_inline(self):
        from django.contrib.auth.models import User

        User.objects.create_superuser("admin6", "admin6@test.com", "admin12345")
        client = Client()
        assert client.login(username="admin6", password="admin12345")
        response = client.get("/admin/services/servicecenter/add/")
        content = response.content.decode()
        assert "phones-TOTAL_FORMS" in content


class TestTagListWidget:
    """Verify the TagListWidget renders and parses correctly."""

    def test_render_empty(self):
        w = TagListWidget(separator="|")
        html = w.render("documents", "", {"id": "id_documents"})
        assert 'type="hidden"' in html
        assert 'name="documents"' in html
        assert 'value=""' in html
        assert "tag-list-add-btn" in html

    def test_render_single_item(self):
        w = TagListWidget(separator="|")
        html = w.render("documents", "doc1", {"id": "id_documents"})
        assert 'value="doc1"' in html
        assert html.count('class="tag-list-item"') == 1

    def test_render_multiple_items(self):
        w = TagListWidget(separator="|")
        html = w.render("documents", "doc1|doc2|doc3", {"id": "id_documents"})
        assert html.count('class="tag-list-item"') == 3
        assert 'value="doc1"' in html
        assert 'value="doc2"' in html
        assert 'value="doc3"' in html

    def test_render_pipe_separator_data_attr(self):
        w = TagListWidget(separator="|")
        html = w.render("documents", "a|b", {"id": "id_documents"})
        assert 'data-separator="|"' in html

    def test_render_comma_separator_data_attr(self):
        w = TagListWidget(separator=",")
        html = w.render("keywords", "kw1,kw2", {"id": "id_keywords"})
        assert 'data-separator=","' in html

    def test_render_escapes_html(self):
        w = TagListWidget(separator="|")
        html = w.render(
            "documents", 'a<script>alert("x")</script>', {"id": "id_documents"}
        )
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_value_from_datadict(self):
        w = TagListWidget(separator="|")
        data = {"documents": "a|b|c"}
        assert w.value_from_datadict(data, {}, "documents") == "a|b|c"

    def test_value_from_datadict_missing(self):
        w = TagListWidget(separator="|")
        assert w.value_from_datadict({}, {}, "documents") == ""

    def test_media_includes_js(self):
        w = TagListWidget(separator="|")
        assert "services/js/admin-taglist-widget.js" in w.media._js

    def test_media_includes_css(self):
        w = TagListWidget(separator="|")
        assert "services/css/admin-rtl.css" in w.media._css.get("all", [])

    def test_media_no_cdn(self):
        w = TagListWidget(separator="|")
        all_urls = " ".join(w.media._css.get("all", [])) + " " + " ".join(w.media._js)
        assert "cdn" not in all_urls.lower()


@pytest.mark.django_db
class TestServiceAdminTagListWidget:
    """Verify the Service admin page renders the tag list widget."""

    def _login(self, username="admin_tl"):
        from django.contrib.auth.models import User

        User.objects.create_superuser(username, f"{username}@test.com", "admin12345")
        client = Client()
        assert client.login(username=username, password="admin12345")
        return client

    def test_admin_add_page_has_taglist_widget(self):
        client = self._login()
        response = client.get("/admin/services/service/add/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "tag-list-widget" in content

    def test_admin_add_page_has_no_cdn(self):
        client = self._login("admin_tl2")
        response = client.get("/admin/services/service/add/")
        content = response.content.decode()
        assert "cdn.jsdelivr.net" not in content

    def test_admin_change_page_has_taglist_widget(self):
        from services.models import Service

        client = self._login("admin_tl3")
        svc = Service.objects.create(
            name="tl-test",
            organization="org",
            documents="d1|d2",
            steps="s1|s2",
            keywords="k1, k2",
        )
        response = client.get(f"/admin/services/service/{svc.id}/change/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "tag-list-widget" in content
        assert "tag-list-item" in content

    def test_admin_add_page_has_taglist_js(self):
        client = self._login("admin_tl4")
        response = client.get("/admin/services/service/add/")
        content = response.content.decode()
        assert "admin-taglist-widget.js" in content
