# Matomo Analytics Setup

This guide covers setting up self-hosted Matomo analytics for the Agahyar
project using Docker Compose.

## Prerequisites

- Docker and Docker Compose installed
- A server with a domain pointed to it (e.g. `analytics.agahyar4iran.ir`)
- The `traefik-network` Docker network already exists:

```bash
docker network create traefik-network
```

## 1. Configure environment variables

Add the Matomo passwords to your `.env` file:

```bash
MATOMO_DB_PASSWORD=your-secure-matomo-db-password
MATOMO_DB_ROOT_PASSWORD=your-secure-matomo-db-root-password
```

## 2. Start Matomo

```bash
docker compose -f docker-compose.matomo.yml up -d
```

This starts two containers:

| Service     | Description                     |
|-------------|---------------------------------|
| `matomo`    | Matomo web application (port 80) |
| `matomo-db` | MySQL 8.0 database backend      |

## 3. Complete the Matomo setup wizard

1. Open `https://analytics.your-domain.com` in your browser.
2. Follow the Matomo setup wizard:
   - **Database**: The connection details are pre-configured via environment
     variables. Just confirm and continue.
   - **Super user**: Create an admin account for the Matomo dashboard.
   - **Website**: Enter the website name (e.g. "Agahyar") and URL
     (e.g. `https://agahyar4iran.ir`).
3. Complete the wizard and log in to the Matomo dashboard.

## 4. Get your Site ID

After completing the wizard:

1. Go to **Administration** (cog icon) > **Websites** > **Manage Websites**.
2. Find your website in the list and note the **Site ID** (the number in
   the ID column).

## 5. Enable tracking on Agahyar

Add the following to your main `.env` file:

```bash
MATOMO_URL=https://analytics.agahyar4iran.ir
MATOMO_SITE_ID=1
```

Replace the URL and Site ID with your actual values.

Then restart the Agahyar web container:

```bash
docker compose -f docker-compose.prod.yml up -d web
```

The Matomo tracking snippet is automatically injected into every page
when both `MATOMO_URL` and `MATOMO_SITE_ID` are set. When they are
empty or unset, no tracking code is rendered.

## 6. Verify tracking

1. Open your Agahyar website in a browser.
2. Navigate to a few pages.
3. Open the Matomo dashboard and check the **Real-Time** widget.
4. You should see your visits appearing within a few seconds.

## Docker network setup

All Matomo containers connect to `traefik-network` (external), which is
shared with the main Agahyar stack and Traefik. Both Matomo and MySQL
communicate over this single network.

## Backup

Matomo data is stored in two Docker volumes:

- `matomo_data` -- Matomo files (plugins, config, tmp).
- `matomo_mysql_data` -- MySQL database with all analytics data.

Back them up with:

```bash
docker compose -f docker-compose.matomo.yml exec matomo-db \
  mysqldump -u root -p matomo > matomo_backup.sql

docker run --rm -v agahyar-project_matomo_data:/data \
  -v $(pwd):/backup alpine tar czf /backup/matomo_data.tar.gz /data
```

## Updating Matomo

To update to a new Matomo version:

```bash
docker compose -f docker-compose.matomo.yml pull matomo
docker compose -f docker-compose.matomo.yml up -d matomo
```

Matomo handles database migrations automatically on startup.

## Troubleshooting

### Matomo shows "Database connection" error

Check that the MySQL container is healthy:

```bash
docker compose -f docker-compose.matomo.yml ps
docker compose -f docker-compose.matomo.yml logs matomo-db
```

### Tracking not working

1. Ensure `MATOMO_URL` and `MATOMO_SITE_ID` are set in `.env`.
2. Restart the web container after changing `.env`.
3. Check the browser developer tools for the Matomo JavaScript loading.
4. Verify the Matomo URL is accessible from the browser.
5. Check that the Site ID matches the one in the Matomo dashboard.

### Matomo not accessible via HTTPS

Ensure Traefik is running and the `analytics.*` DNS record points to
your server. Check Traefik logs:

```bash
docker logs traefik --tail 50
```
