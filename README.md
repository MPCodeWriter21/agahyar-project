# 🏛️ Aghahyār (آگاه‌یار)

**Smart Citizen Information System for Government Services**

---

## 📖 About the Project

**Aghahyār** is a web-based platform designed to help citizens easily access accurate information about government services before visiting offices in person.

It provides clear details about **required documents**, **steps**, **costs**, **estimated time**, and the **nearest service centers** – all in one place.

> **Problem:** Millions of unsuccessful office visits happen every year due to a lack of awareness.  
> **Solution:** Aghahyār empowers citizens with knowledge, saving time, money, and reducing frustration for both people and government employees.

---

## 👁️ Vision

To become the **leading citizen‑friendly information hub** for all public services in Iran, bridging the gap between people and government with transparency, simplicity, and intelligence.

---

## ✨ Key Features

- **🔍 Smart Search** – Find any government service by name or keyword  
- **📋 Service Details** – View required documents, steps, cost, and duration  
- **📍 Nearest Centers** – Automatically shows the closest service center based on the user’s city and neighborhood  
- **🗺️ Google Maps Integration** – Direct link to the center’s location  
- **👤 User Authentication** – Sign up / Login with city & neighborhood storage  
- **🧠 AI‑Powered Suggestions** – Simulated intelligence for recommending nearby centers  
- **📱 Fully Responsive** – Works perfectly on mobile, tablet, and desktop  
- **🖥️ Admin Panel** – Manage services, FAQs, and centers easily via Django admin

---

## 🧱 Project Structure
agahyar-project/
├── agahyar_project/ # Django project settings
├── services/ # Main application
│ ├── models.py # Service, UserProfile, FAQ, ServiceCenter
│ ├── views.py # All logic (search, detail, nearby, auth)
│ ├── scraper.py # Nearest centers logic + AI simulation
│ ├── urls.py # App routes
│ └── admin.py # Admin panel registration
├── templates/services/ # All HTML templates
│ ├── base.html # Main layout
│ ├── home.html # Homepage with search & popular services
│ ├── search.html # Search results
│ ├── detail.html # Service details + nearest center
│ ├── nearby_centers.html # List of all centers with nearest label
│ └── ...
├── static/ # CSS, JS, images (if any)
├── db.sqlite3 # SQLite database
├── manage.py
├── requirements.txt
└── README.md

---

## 🛠️ Technologies Used

- **🐍 Python 3.12** – Core programming language  
- **🧩 Django 6.0** – High‑level web framework  
- **🗄️ SQLite** – Lightweight database (development)  
- **🎨 HTML5 / CSS3 / JavaScript** – Frontend UI  
- **📦 Git & GitHub** – Version control and collaboration  
- **☁️ Render / PythonAnywhere** – Planned deployment platforms  

---

## 🖼️ Project Preview

*(You can place your screenshots here – just replace the placeholder links)*

| Homepage | Search Results | Service Details |
|:--------:|:--------------:|:---------------:|
| ![Homepage](screenshots/home.png) | ![Search](screenshots/search.png) | ![Detail](screenshots/detail.png) |

> 💡 *Tip: Upload your images to the `screenshots/` folder and link them here.*

---

## 🚀 How to Run the Project (Local Setup)

Follow these steps to run the project on your own machine:

```bash
# 1. Clone the repository
git clone https://github.com/Fatemehmohammadganji/agahyar-project.git

# 2. Go to the project folder
cd agahyar-project

# 3. Create a virtual environment
python -m venv venv

# 4. Activate the virtual environment
venv\Scripts\activate        # On Windows
# source venv/bin/activate   # On Mac / Linux

# 5. Install dependencies
pip install -r requirements.txt

# 6. Apply database migrations
python manage.py migrate

# 7. Create a superuser (admin)
python manage.py createsuperuser

# 8. Run the development server
python manage.py runserver
```

Then open your browser and visit:
👉 http://127.0.0.1:8000

🗺️ Future Plans & Roadmap
We are committed to continuously improving Aghahyār. Here are our goals for the coming months:

Real AI Integration – Use OpenAI / Google Maps API for dynamic nearest-center detection

Mobile App – Develop a native Android / iOS app for wider accessibility

Multi-City Support – Add service centers for all major cities in Iran

Admin Dashboard – Visual analytics for user activity and service popularity

User Feedback System – Allow citizens to rate services and leave comments

Advanced Security – OAuth2 login, password recovery, and two-factor authentication

Multi-Language – Support English and other languages for international users
🤝 Team Members
Fatemeh Mohammadi Ganjii – Project Manager & Frontend Developer

Zahra Kamalian – Backend Developer

Mohsen Ali Ahmadi – Database Developer & Organization Liaison

