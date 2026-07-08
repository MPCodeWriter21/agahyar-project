#!/usr/bin/env bash
# Download vendored static assets from CDN into static/
# Run this during Docker build or locally on Linux/macOS.
set -euo pipefail

CDN="https://unpkg.com"

# Leaflet 1.9.4
echo "Downloading Leaflet ..."
mkdir -p static/libs/leaflet
curl -fsSL "$CDN/leaflet@1.9.4/dist/leaflet.js" -o static/libs/leaflet/leaflet.js
curl -fsSL "$CDN/leaflet@1.9.4/dist/leaflet.css" -o static/libs/leaflet/leaflet.css
mkdir -p static/libs/leaflet/images
curl -fsSL "$CDN/leaflet@1.9.4/dist/images/layers-2x.png" -o static/libs/leaflet/images/layers-2x.png
curl -fsSL "$CDN/leaflet@1.9.4/dist/images/layers.png" -o static/libs/leaflet/images/layers.png
curl -fsSL "$CDN/leaflet@1.9.4/dist/images/marker-icon-2x.png" -o static/libs/leaflet/images/marker-icon-2x.png
curl -fsSL "$CDN/leaflet@1.9.4/dist/images/marker-icon.png" -o static/libs/leaflet/images/marker-icon.png
curl -fsSL "$CDN/leaflet@1.9.4/dist/images/marker-shadow.png" -o static/libs/leaflet/images/marker-shadow.png

# OpenLayers 7.2.2
echo "Downloading OpenLayers ..."
mkdir -p static/libs/ol
curl -fsSL "$CDN/ol@7.2.2/dist/ol.js" -o static/libs/ol/ol.js
curl -fsSL "$CDN/ol@7.2.2/ol.css" -o static/libs/ol/ol.css

# Font Awesome 6.7.2
echo "Downloading Font Awesome ..."
mkdir -p static/libs/fontawesome/css static/libs/fontawesome/webfonts
curl -fsSL "$CDN/@fortawesome/fontawesome-free@6.7.2/css/all.min.css" -o static/libs/fontawesome/css/fontawesome-all.min.css
for f in \
  fa-brands-400.ttf fa-brands-400.woff2 \
  fa-regular-400.ttf fa-regular-400.woff2 \
  fa-solid-900.ttf fa-solid-900.woff2 \
  fa-v4compatibility.ttf fa-v4compatibility.woff2; do
  curl -fsSL "$CDN/@fortawesome/fontawesome-free@6.7.2/webfonts/$f" -o "static/libs/fontawesome/webfonts/$f"
done

# Alpine.js 3.14.9
echo "Downloading Alpine.js ..."
mkdir -p static/libs
curl -fsSL "$CDN/alpinejs@3.14.9/dist/cdn.min.js" -o static/libs/alpine.min.js


# Vazirmatn 33.0.3
echo "Downloading Vazirmatn ..."
curl -fsSL "$CDN/vazirmatn@33.0.3/fonts/webfonts/Vazirmatn-Regular.woff2" -o static/Vazirmatn-Regular.woff2

# Toastify 1.12.0
echo "Downloading Toastify ..."
mkdir -p static/libs/toastify
curl -fsSL "$CDN/toastify-js@1.12.0/src/toastify.js" -o static/libs/toastify/toastify.js
curl -fsSL "$CDN/toastify-js@1.12.0/src/toastify.css" -o static/libs/toastify/toastify.css

echo "Done."
