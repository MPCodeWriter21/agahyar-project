# Use PostGIS

- STATUS: OPEN
- PRIORITY: 70
- TAGS: PostGIS, database, location

Use PostGIS for the database.
This will help us with managing the locations properly.
We could also add an option to the profile page for the users to choose their location on the map.

This task will remove the manual running of the project and will put SQLite away.
For development, we will use `docker-compose.dev.yml` and the production is with docker as well.
It is important to be sure that the docker setup is perfect and can handle active development.

Related: Task(20260705-131600)
