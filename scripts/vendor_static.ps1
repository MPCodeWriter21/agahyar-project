# Download vendored static assets from CDN into static/
# Run this on Windows after pulling when static/libs/ is missing.
$CDN = "https://unpkg.com"

# Leaflet 1.9.4
Write-Host "Downloading Leaflet ..."
$null = New-Item -ItemType Directory -Force -Path static/libs/leaflet/images
Invoke-WebRequest -Uri "$CDN/leaflet@1.9.4/dist/leaflet.js" -OutFile static/libs/leaflet/leaflet.js
Invoke-WebRequest -Uri "$CDN/leaflet@1.9.4/dist/leaflet.css" -OutFile static/libs/leaflet/leaflet.css
Invoke-WebRequest -Uri "$CDN/leaflet@1.9.4/dist/images/layers-2x.png" -OutFile static/libs/leaflet/images/layers-2x.png
Invoke-WebRequest -Uri "$CDN/leaflet@1.9.4/dist/images/layers.png" -OutFile static/libs/leaflet/images/layers.png
Invoke-WebRequest -Uri "$CDN/leaflet@1.9.4/dist/images/marker-icon-2x.png" -OutFile static/libs/leaflet/images/marker-icon-2x.png
Invoke-WebRequest -Uri "$CDN/leaflet@1.9.4/dist/images/marker-icon.png" -OutFile static/libs/leaflet/images/marker-icon.png
Invoke-WebRequest -Uri "$CDN/leaflet@1.9.4/dist/images/marker-shadow.png" -OutFile static/libs/leaflet/images/marker-shadow.png

# OpenLayers 7.2.2
Write-Host "Downloading OpenLayers ..."
$null = New-Item -ItemType Directory -Force -Path static/libs/ol
Invoke-WebRequest -Uri "$CDN/ol@7.2.2/dist/ol.js" -OutFile static/libs/ol/ol.js
Invoke-WebRequest -Uri "$CDN/ol@7.2.2/ol.css" -OutFile static/libs/ol/ol.css

# Font Awesome 6.7.2
Write-Host "Downloading Font Awesome ..."
$null = New-Item -ItemType Directory -Force -Path static/libs/fontawesome/css, static/libs/fontawesome/webfonts
Invoke-WebRequest -Uri "$CDN/@fortawesome/fontawesome-free@6.7.2/css/all.min.css" -OutFile static/libs/fontawesome/css/fontawesome-all.min.css
$fontFiles = @(
  "fa-brands-400.ttf", "fa-brands-400.woff2",
  "fa-regular-400.ttf", "fa-regular-400.woff2",
  "fa-solid-900.ttf", "fa-solid-900.woff2",
  "fa-v4compatibility.ttf", "fa-v4compatibility.woff2"
)
foreach ($f in $fontFiles) {
  Invoke-WebRequest -Uri "$CDN/@fortawesome/fontawesome-free@6.7.2/webfonts/$f" -OutFile "static/libs/fontawesome/webfonts/$f"
}

# Alpine.js 3.14.9
Write-Host "Downloading Alpine.js ..."
$null = New-Item -ItemType Directory -Force -Path static/libs
Invoke-WebRequest -Uri "$CDN/alpinejs@3.14.9/dist/cdn.min.js" -OutFile static/libs/alpine.min.js

# Vazirmatn 33.0.3
Write-Host "Downloading Vazirmatn ..."
Invoke-WebRequest -Uri "$CDN/vazirmatn@33.0.3/fonts/webfonts/Vazirmatn-Regular.woff2" -OutFile static/Vazirmatn-Regular.woff2

# Toastify 1.12.0
Write-Host "Downloading Toastify ..."
$null = New-Item -ItemType Directory -Force -Path static/libs/toastify
Invoke-WebRequest -Uri "$CDN/toastify-js@1.12.0/src/toastify.js" -OutFile static/libs/toastify/toastify.js
Invoke-WebRequest -Uri "$CDN/toastify-js@1.12.0/src/toastify.css" -OutFile static/libs/toastify/toastify.css

# Swagger UI 5.32.8
Write-Host "Downloading Swagger UI ..."
$SWAGGER_CDN = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.32.8"
$null = New-Item -ItemType Directory -Force -Path static/libs/swagger-ui
Invoke-WebRequest -Uri "$SWAGGER_CDN/swagger-ui-bundle.js" -OutFile static/libs/swagger-ui/swagger-ui-bundle.js
Invoke-WebRequest -Uri "$SWAGGER_CDN/swagger-ui-standalone-preset.js" -OutFile static/libs/swagger-ui/swagger-ui-standalone-preset.js
Invoke-WebRequest -Uri "$SWAGGER_CDN/swagger-ui.css" -OutFile static/libs/swagger-ui/swagger-ui.css
Invoke-WebRequest -Uri "$SWAGGER_CDN/favicon-32x32.png" -OutFile static/libs/swagger-ui/favicon-32x32.png

Write-Host "Done."
