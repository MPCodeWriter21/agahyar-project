/* Admin map widget enhancements: Neshan search and lat/lng coordinate inputs */

(function () {
  "use strict";

  var DEBOUNCE_MS = 400;
  var SEARCH_URL = "/admin/neshan-search/";

  function debounce(fn, ms) {
    var timer;
    return function () {
      var ctx = this;
      var args = arguments;
      clearTimeout(timer);
      timer = setTimeout(function () {
        fn.apply(ctx, args);
      }, ms);
    };
  }

  function pointToLatLng(geometry) {
    if (!geometry) return null;
    var coords = null;
    var type = geometry.getType();
    if (type === "Point") {
      coords = geometry.getCoordinates();
    } else if (type === "Polygon") {
      coords = geometry.getCoordinates()[0][0];
    } else if (type === "MultiPolygon") {
      coords = geometry.getCoordinates()[0][0][0];
    }
    if (coords && coords.length >= 2) {
      var lonlat = ol.proj.transform(coords, "EPSG:3857", "EPSG:4326");
      return { lat: lonlat[1], lng: lonlat[0] };
    }
    return null;
  }

  function latLngToPoint(lat, lng) {
    var xy = ol.proj.transform([lng, lat], "EPSG:4326", "EPSG:3857");
    return new ol.geom.Point(xy);
  }

  // Patch initMapWidgetInSection to store widget instances on wrapper elements.
  // This runs at load time, before DOMContentLoaded fires.
  if (typeof initMapWidgetInSection === "function") {
    var _origInit = initMapWidgetInSection;
    initMapWidgetInSection = function (section) {
      var maps = _origInit(section);
      section
        .querySelectorAll(".dj_map_wrapper")
        .forEach(function (wrapper, idx) {
          if (maps[idx]) {
            wrapper._mapWidget = maps[idx];
          }
        });
      return maps;
    };
  }

  function enhanceCoordInputs(wrapper) {
    if (wrapper._coordEnhanced) return;
    wrapper._coordEnhanced = true;

    var textarea = wrapper.querySelector("textarea");
    if (!textarea) return;
    var id = textarea.id;
    var searchInput = document.getElementById(id + "_search");
    var resultsDiv = document.getElementById(id + "_search_results");
    var latInput = document.getElementById(id + "_lat_input");
    var lngInput = document.getElementById(id + "_lng_input");
    if (!searchInput || !resultsDiv || !latInput || !lngInput) return;

    var mapWidget = wrapper._mapWidget;
    if (!mapWidget) return;

    function syncInputsToMap(geometry) {
      var ll = pointToLatLng(geometry);
      if (ll) {
        latInput.value = ll.lat.toFixed(6);
        lngInput.value = ll.lng.toFixed(6);
      }
    }

    function setPointOnMap(lat, lng) {
      var features = mapWidget.featureOverlay.getSource().getFeatures();
      var pt = latLngToPoint(lat, lng);

      if (features.length > 0) {
        features[0].setGeometry(pt);
      } else {
        var feat = new ol.Feature({ geometry: pt });
        mapWidget.featureOverlay.getSource().addFeature(feat);
      }

      var lonlat = ol.proj.transform([lng, lat], "EPSG:4326", "EPSG:3857");
      mapWidget.map.getView().setCenter(lonlat);
      mapWidget.map.getView().setZoom(15);

      syncInputsToMap(
        mapWidget.featureOverlay.getSource().getFeatures()[0].getGeometry(),
      );
    }

    // Listen for feature changes and sync inputs
    mapWidget.featureCollection.on("add", function (evt) {
      evt.element.on("change", function () {
        syncInputsToMap(this.getGeometry());
      });
    });

    // Sync inputs if a point already exists
    var existing = mapWidget.featureOverlay.getSource().getFeatures();
    if (existing.length > 0) {
      syncInputsToMap(existing[0].getGeometry());
    }

    // --- Coordinate input handlers ---
    function onCoordInputChange() {
      var lat = parseFloat(latInput.value);
      var lng = parseFloat(lngInput.value);
      if (isNaN(lat) || isNaN(lng)) return;
      if (lat < -90 || lat > 90 || lng < -180 || lng > 180) return;
      setPointOnMap(lat, lng);
    }

    latInput.addEventListener("change", onCoordInputChange);
    lngInput.addEventListener("change", onCoordInputChange);

    // --- Search handlers ---
    function doSearch() {
      var term = searchInput.value.trim();
      if (!term) {
        resultsDiv.style.display = "none";
        resultsDiv.innerHTML = "";
        return;
      }

      // Use current point as reference for Neshan search
      var refLat = 35.6892;
      var refLng = 51.389;
      var existingFeats = mapWidget.featureOverlay.getSource().getFeatures();
      if (existingFeats.length > 0) {
        var ll = pointToLatLng(existingFeats[0].getGeometry());
        if (ll) {
          refLat = ll.lat;
          refLng = ll.lng;
        }
      }

      var url =
        SEARCH_URL +
        "?term=" +
        encodeURIComponent(term) +
        "&lat=" +
        refLat +
        "&lng=" +
        refLng;

      fetch(url)
        .then(function (r) {
          return r.json();
        })
        .then(function (data) {
          if (data.error) {
            resultsDiv.innerHTML =
              '<div class="neshan-search-item neshan-search-error">' +
              data.error +
              "</div>";
            resultsDiv.style.display = "block";
            return;
          }
          var items = data.items || [];
          if (items.length === 0) {
            resultsDiv.innerHTML =
              '<div class="neshan-search-item neshan-search-empty">\u0646\u062a\u06cc\u062c\u0647\u200c\u0627\u06cc \u06cc\u0627\u0641\u062a \u0646\u0634\u062f</div>';
            resultsDiv.style.display = "block";
            return;
          }
          var html = "";
          for (var i = 0; i < items.length; i++) {
            var item = items[i];
            html +=
              '<div class="neshan-search-item" data-lat="' +
              item.location.y +
              '" data-lng="' +
              item.location.x +
              '">' +
              '<span class="neshan-search-title">' +
              (item.title || "") +
              "</span>" +
              '<span class="neshan-search-address">' +
              (item.address || "") +
              "</span>" +
              "</div>";
          }
          resultsDiv.innerHTML = html;
          resultsDiv.style.display = "block";
        })
        .catch(function () {
          resultsDiv.innerHTML =
            '<div class="neshan-search-item neshan-search-error">\u062e\u0637\u0627 \u062f\u0631 \u062c\u0633\u062a\u062c\u0648</div>';
          resultsDiv.style.display = "block";
        });
    }

    searchInput.addEventListener("input", debounce(doSearch, DEBOUNCE_MS));
    searchInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        doSearch();
      }
    });

    var searchBtn = document.getElementById(id + "_search_btn");
    if (searchBtn) {
      searchBtn.addEventListener("click", function () {
        doSearch();
      });
    }

    resultsDiv.addEventListener("click", function (e) {
      var item = e.target.closest(".neshan-search-item");
      if (
        !item ||
        item.classList.contains("neshan-search-error") ||
        item.classList.contains("neshan-search-empty")
      )
        return;
      var lat = parseFloat(item.getAttribute("data-lat"));
      var lng = parseFloat(item.getAttribute("data-lng"));
      if (isNaN(lat) || isNaN(lng)) return;

      setPointOnMap(lat, lng);
      searchInput.value = item.querySelector(
        ".neshan-search-title",
      ).textContent;
      resultsDiv.style.display = "none";
      resultsDiv.innerHTML = "";
    });

    // Close results when clicking outside
    document.addEventListener("click", function (e) {
      if (!searchInput.contains(e.target) && !resultsDiv.contains(e.target)) {
        resultsDiv.style.display = "none";
      }
    });

    // Patch "Delete all Features" link to also clear inputs
    var clearLink = wrapper.querySelector(".clear_features a");
    if (clearLink) {
      clearLink.addEventListener("click", function () {
        setTimeout(function () {
          latInput.value = "";
          lngInput.value = "";
        }, 50);
      });
    }
  }

  function init() {
    document
      .querySelectorAll(".neshan-widget-wrapper")
      .forEach(function (wrapper) {
        if (wrapper._coordEnhanced) return;
        enhanceCoordInputs(wrapper);
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    // Give initMapWidgetInSection time to run first
    setTimeout(init, 200);

    // Watch for dynamically added widgets (inline formsets)
    var observer = new MutationObserver(function (mutations) {
      var needsReinit = false;
      for (var i = 0; i < mutations.length; i++) {
        if (mutations[i].addedNodes.length) {
          needsReinit = true;
          break;
        }
      }
      if (needsReinit) {
        setTimeout(init, 100);
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
  });
})();
