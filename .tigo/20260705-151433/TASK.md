# Use PostGIS

- STATUS: COMPLETED
- PRIORITY: 70
- TAGS: PostGIS, database, location

Use PostGIS for the database.
This will help us with managing the locations properly.
We could also add an option to the profile page for the users to choose their location on the map.

This task will remove the manual running of the project and will put SQLite away.
For development, we will use `docker-compose.dev.yml` and the production is with docker as well.
It is important to be sure that the docker setup is perfect and can handle active development.

## What was done

### Infrastructure
- Changed `docker-compose.dev.yml` db image from `postgres:17-alpine` to `postgis/postgis:17-3.4`
- Added `gdal-dev geos-dev proj-dev` system dependencies to the Dockerfile builder stage
- Added `gdal geos proj` system packages to the Dockerfile runtime stage
- Updated `.env` and `.env.example` to use `django.contrib.gis.db.backends.postgis`

### Django settings
- Added `django.contrib.gis` to `INSTALLED_APPS`
- Changed default `DB_ENGINE` to `django.contrib.gis.db.backends.postgis`

### Model changes (ServiceCenter)
- Removed `latitude` (FloatField) and `longitude` (FloatField) fields
- Changed `coordinate` from `CharField` (storing `"lat,lng"` text) to `PointField` (srid=4326)
- Updated `get_map_url()` to use `self.coordinate.y` (lat) and `self.coordinate.x` (lng)

### Migration
- Created `0008_postgis_coordinate.py`:
  1. Adds a temporary `coordinate_new` PointField
  2. Data migration to parse existing `coordinate` strings and `latitude`/`longitude` floats into Point objects
  3. Removes `latitude`, `longitude`, and old `coordinate` CharField
  4. Renames `coordinate_new` to `coordinate`

### Scripts
- Updated `scripts/populate_services.py` to create `Point(float(lng), float(lat), srid=4326)` objects

### Tests
- Added tests for `get_map_url()` with and without coordinate
- All 148 tests pass

Related: Task(20260705-131600)
