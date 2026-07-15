# Move away from hardcoded limited cities

- STATUS: CLOSED
- PRIORITY: 65
- TAGS: enhancement

The cities that are supported by the project must be determined based on the cities that have at least one Service Center in the database.

We might not actually need a location for cities, since the Service Centers are very likely to provide their own locations in which case we can probably strip the hard coded city locations from the code.
