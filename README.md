# Aghahyar (آگاه‌یار)

Smart Citizen Information System for Government Services.

## About the Project

**Aghahyar** helps citizens access accurate information about government
services before visiting offices in person — showing **required documents**,
**steps**, **costs**, **duration**, and **nearest service centers** in one
place.

> **Problem:** Millions of unsuccessful office visits happen every year due to
> lack of awareness.
> **Solution:** Aghahyar empowers citizens with knowledge, saving time, money,
> and reducing frustration.

## Key Features

- **Smart Search** – Find services by name, organization, or city
- **Service Details** – Documents, steps, cost, and duration for each service
- **Nearest Centers** – Closest service center based on user's city and
  neighborhood with Google Maps links
- **User Authentication** – Sign up / Login with city & neighborhood storage
- **Rating & Feedback** – Rate services 1–5 stars and leave public comments
- **Bookmark Services** – Save favorite services for quick access
- **Print-Friendly View** – Clean print layout for service details
- **Dark/Light Theme** – Per-device theme with localStorage persistence
- **Persian Error Messages** – Backend error codes map to Persian text
- **Security Hardening** – Rate limiting, CSP headers, configurable admin URL,
  secure session settings
- **Fully Responsive** – Works on mobile, tablet, and desktop
- **Admin Panel** – Manage services, FAQs, and centers via Django admin

## Technologies Used

- **Python 3.12 / Django 6.0** – Backend
- **uv** – Python package manager
- **PostgreSQL / SQLite** – Database
- **Redis** – Cache & sessions (production)
- **Docker** – Containerized development and deployment
- **HTML5 / CSS3 / JavaScript (vanilla)** – Frontend; Font Awesome icons
- **Gunicorn** – Production WSGI server

## Project Preview

### Login

![Login page](images/loginpage.png)

### Home

![Home page](images/homepage.png)

### Services

![Services page](images/servicepage.png)

### Service Details

![Service details](images/service-info.png)

### About

![About page](images/about.png)

### FAQ

![FAQ page](images/faq.png)

### Contact

![Contact page](images/contact.png)

### Nearest Centers

![Nearest centers page](images/nearestplace.png)

#### Resources used for the screenshots

- [Background Picture](https://unsplash.com/photos/grey-sand-wave-RCAhiGJsUUE)
- [Screenshot Extension](https://screenshot.rocks/)

## How to Run the Project (Local Setup)

## Quick Start

```bash
git clone https://github.com/Fatemehmohammadganji/agahyar-project.git
cd agahyar-project

# Install uv (if needed): https://docs.astral.sh/uv/
uv venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv sync
cp .env.example .env
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Populate sample data (optional):

```bash
uv run python scripts/populate_services.py
uv run python scripts/populate_centers.py
uv run python scripts/populate_faq.py
```

Visit **<http://127.0.0.1:8000>** in your browser.

Run tests:

```bash
uv run pytest
```

## Project Structure

```
agahyar-project/
├── src/                    # Python packages
│   ├── agahyar_project/    # Django project config
│   └── services/           # Main app (models, views, forms, etc.)
├── templates/
│   └── services/           # HTML templates
├── static/services/        # CSS, JS, fonts, icons (no CDN)
├── scripts/                # Database population scripts
└── docker-compose*.yml     # Dev & production Docker configs
```

## Roadmap

- [ ] Real AI integration (OpenAI / Google Maps API) for dynamic center
      detection
- [ ] Mobile app (Android / iOS)
- [ ] Multi-city support (all major Iranian cities)
- [ ] Multi-language (English and other languages)
- [ ] OAuth2 login and two-factor authentication
- [ ] Notification system for service updates

## Team

- Fatemeh Mohammadganji – Project Manager & Frontend Developer
- Zahra Kamalian – Backend Developer
- Mohsen Ali Ahmadi – Database Developer & Organization Liaison
