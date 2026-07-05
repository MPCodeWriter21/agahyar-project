# Add maps

- STATUS: OPEN
- PRIORITY: 65
- TAGS: map, feature, enhancement

Use leafletjs to show maps.
In a service's page we should show the map of the current city and mark all the centers offering that service.
The coordinate field will help a lot here.
We may need to use an API to find out where on the map  we should focus on to show the whole city.
We could use openstreetmap or Neshan API (Neshan provides a free API key with more credit than we'll ever need but we should still cache all the results we can and avoid sending duplicate requests).
