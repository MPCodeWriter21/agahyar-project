# Move away from hardcoded limited cities

- STATUS: OPEN
- PRIORITY: 65
- TAGS: enhancement

The cities that are supported by the project must be determined based on the cities that have at least one Service Center in the database.

Also, the location of a lot of cities might have to be hardcoded or we might want to use an API to request the location of the city on demand.
We might not actually need a location for cities, since the Service Centers are very likely to provide their own locations in which case we can probably strip the hard coded city locations from the code.
