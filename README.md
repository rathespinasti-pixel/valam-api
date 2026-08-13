# Valam (வளம்) — Smart Agriculture REST API Backend

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-3.1.1-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-Extended-000000?style=for-the-badge&logo=json-web-tokens&logoColor=white)
![Swagger](https://img.shields.io/badge/Swagger-OpenAPI--3.0-85EA2D?style=for-the-badge&logo=swagger&logoColor=black)

**Valam (வளம்)** is a comprehensive, production-ready Python Flask RESTful backend service designed for smart agricultural management, digital crop tracking, direct farmer-to-consumer cloud marketplace transactions, AI agronomy advice, plant disease diagnosis, and smart solar-powered irrigation planning.

---

## 🌟 Key Platform Features

### 👤 1. Multi-Role Authentication & User Profiles
- **Role-Based Access Control (RBAC)**: Supports `Farmer`, `Consumer`, `Admin`, and `Super Admin` roles.
- **JWT Token Management**: Access tokens with rotation and expiration controls, stateless blacklisting, and secure hashing.
- **District & Farm Localization**: Profile tracking tuned for Sri Lankan provinces (e.g. Vavuniya, Jaffna, Kilinochchi, Trincomalee, Badulla) and crop scale (acres/hectares).

### 🌾 2. Crop Tracking & 5-Stage Growth Lifecycle
- **5-Stage Growth Tracker**: Tracks crops from Stage 1 (*Seedling / Nursery*), Stage 2 (*Vegetative / Growth*), Stage 3 (*Flowering*), Stage 4 (*Fruiting & Dosing*), to Stage 5 (*Harvest*).
- **Dynamic Agronomic Dosing**: Calculates exact compost recipes (Organic vs Non-Organic/Chemical), water requirements (L/plant/day), and pest alerts tailored per stage.
- **Progress Line & Timeline Visualizer**: Automatic progress percentage calculations based on planting date and expected total days to harvest.

### 🤖 3. AI Farming Assistant & Plant Disease Diagnosis
- **Gemini AI Integration**: Multi-lingual AI chatbot (English, Tamil 🇱🇰, Sinhala 🇱🇰) trained on Dry Zone agriculture, soil profiles, and localized pest management.
- **Vision-Based Disease Diagnosis**: Upload crop photos to run AI disease detection, severity scoring, symptoms breakdown, and organic treatment recommendations.

### 🛒 4. Produce Cloud Marketplace & Real-Time Bargaining
- **Direct Farmer-to-Consumer Produce Listings**: Post produce with crop variety, harvest date, location, bulk quantity, unit pricing, and quality photos.
- **Interactive Offer Bargaining Engine**: Buyers submit price offers per kg; farmers receive real-time offer notifications to **Accept**, **Reject**, or submit **Counter-Offers**.
- **1-on-1 Direct Messaging**: Integrated private chat channel between buyer and seller once an offer is initiated or accepted.

### ☀️ 5. Smart Irrigation & Solar Pumping Sizing Calculator
- **Automated Sizing Engine**: Computes required solar panel wattage (kW), pump horsepower (HP), and drip emitter layout based on acreage, crop spacing (cm), and water depth.
- **Government Subsidy Advisor**: Checks eligibility for Agrarian Services Department grants and co-operative bulk subsidies.

### 💬 6. Community Forum & Admin Broadcast Center
- **Farmer Community Hub**: Categorized discussion threads (*Pest Control*, *Organic Fertilizer*, *Marketplace Prices*, *Weather Advice*) with comments and upvotes.
- **Broadcast System Notifications**: System-wide push/in-app alert broadcasting for monsoon rain warnings, market price surges, and pest outbreaks.

---

## 🏗️ Project Architecture & Directory Structure

```text
valam-api/
├── app/
│   ├── __init__.py            # Application factory, CORS, JWT & Blueprint registration
│   ├── config.py              # Environment configuration loader (MySQL / Postgres / SQLite)
│   ├── extensions.py          # Central SQLAlchemy, JWTManager, Migrations instances
│   ├── models/                # Database models & ORM entities
│   │   ├── user.py            # User model (roles, district, contact, password hash)
│   │   ├── crop.py            # Farmer active crop tracker & 5-stage lifecycle state
│   │   ├── crop_guide.py      # Master agronomic crop guide dataset & compost recipes
│   │   ├── diagnosis.py       # Plant disease diagnosis uploads & catalog
│   │   ├── marketplace_models.py # Produce listings, bargain offers, direct chat messages
│   │   ├── community.py       # Forum discussion topics and replies
│   │   ├── solar_guide.py     # Solar pumping & irrigation specifications
│   │   └── product.py         # Agricultural tools & equipment listings
│   ├── routes/                # REST API Endpoint Controller Blueprints
│   │   ├── auth.py            # Registration, login, token refresh, logout
│   │   ├── users.py           # Profile update, settings, password change
│   │   ├── crops.py           # Active farmer cultivation tracking
│   │   ├── managed_crops.py   # Crop lifecycle stage updates & automated stage alerts
│   │   ├── crop_guides.py     # Master agronomic crop guide search & stage compost lookup
│   │   ├── diagnosis.py       # AI plant disease diagnosis endpoints
│   │   ├── cloud_market.py    # Produce listings & bargaining offer negotiation engine
│   │   ├── direct_chat.py     # 1-on-1 buyer-seller direct messaging
│   │   ├── user_notifications.py # In-app notification center & unread counts
│   │   ├── community.py       # Forum discussions & nested comment replies
│   │   ├── chatbot.py         # AI farming assistant console
│   │   ├── solar.py           # Solar pump & irrigation recommendation engine
│   │   ├── weather.py         # Real-time weather advisories per district
│   │   └── admin.py           # Administrative management, crop database & broadcast alerts
│   └── utils/
│       ├── decorators.py      # Role-checking (@admin_required, @farmer_required)
│       ├── ai_client.py       # Gemini API client integration for agronomy
│       └── weather_client.py  # Weather data provider wrapper
├── seed_admin.py              # Command-line utility to securely seed Super Admin account
├── seed_vavuniya_data.py      # Master Agronomic Seed Data (Northern Province crops & guides)
├── run.py                     # Entry point & automatic database schema synchronizer
├── requirements.txt           # Python dependency specifications
├── .env.example               # Template environment configuration file
├── Procfile                   # Gunicorn process file for cloud deployment (Heroku / Render)
└── railway.json               # Railway cloud deployment configuration
```

---

## ⚡ Quickstart & Setup Guide

### 1. Prerequisites
- **Python 3.11+** installed
- **Git** installed
- **MySQL / PostgreSQL** (Optional — defaults to local SQLite if unavailable)

### 2. Environment Setup & Virtual Environment Creation

Clone the repository and enter the backend directory:
```bash
git clone https://github.com/your-org/valam-api.git
cd valam-api
```

Create and activate a virtual environment:
```bash
# On Windows (PowerShell / Command Prompt):
python -m venv .venv
.\.venv\Scripts\activate

# On Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to create your local `.env` configuration:
```bash
# On Windows PowerShell:
Copy-Item .env.example .env

# On Linux / macOS:
cp .env.example .env
```

Edit `.env` with your preferred configuration:
```ini
# Application Secrets
SECRET_KEY=valam-super-secret-key-2026
JWT_SECRET_KEY=valam-jwt-secret-key-2026
FLASK_ENV=development

# Database Connection (MySQL / PostgreSQL / SQLite)
# Defaults to SQLite if DATABASE_URL is not specified: sqlite:///valam_local.db
DATABASE_URL=sqlite:///valam_local.db

# AI & Third-Party API Keys
GEMINI_API_KEY=your_gemini_api_key_here
WEATHER_API_KEY=your_open_weather_api_key_here

# Super Administrator Seed Credentials
ADMIN_EMAIL=admin@valam.lk
ADMIN_PASSWORD=AdminSecurePass123!
ADMIN_NAME=Super Administrator
```

### 4. Seed Database & Master Data

Populate the database with master agronomic crop guides, 5-stage compost recommendations, disease catalog, and default admin accounts:
```bash
# 1. Seed Agronomic Guides & Vavuniya Dry Zone Crop Master Dataset
python seed_vavuniya_data.py

# 2. Securely Provision Administrator Account
python seed_admin.py
```

### 5. Start Development API Server

Run the Flask application:
```bash
python run.py
```

The API backend will start at **`http://localhost:5000`**.
Interactive Swagger API documentation will be available at **`http://localhost:5000/api/docs/`**.

---

## 📡 REST API Endpoint Summary

| Category | Endpoint | Method | Access | Description |
| :--- | :--- | :---: | :---: | :--- |
| **Auth** | `/api/auth/register` | `POST` | Public | Register new `Farmer` or `Consumer` account |
| **Auth** | `/api/auth/login` | `POST` | Public | Authenticate user & return JWT token pair |
| **Auth** | `/api/auth/me` | `GET` | Authenticated | Fetch authenticated user profile & role |
| **Users** | `/api/users/profile` | `PUT` | Authenticated | Update district, contact number, or full name |
| **Crops** | `/api/crops` | `GET`, `POST` | Farmer | List or register new active crop cultivation |
| **Managed Crops**| `/api/managed-crops/<id>` | `GET`, `PUT` | Farmer | Retrieve 5-stage lifecycle state or advance stage |
| **Crop Guides** | `/api/crop-guides` | `GET` | Public | Search master agronomic database & stage composts |
| **Diagnosis** | `/api/diagnosis/analyze` | `POST` | Farmer | Run AI disease detection on uploaded leaf photo |
| **Cloud Market** | `/api/cloud-market/listings` | `GET`, `POST` | Public / Farmer | View or post produce marketplace listings |
| **Cloud Market** | `/api/cloud-market/offers` | `POST`, `PUT` | Authenticated | Submit price bargain offer or update offer status |
| **Direct Chat** | `/api/chat/conversations` | `GET`, `POST` | Authenticated | List chat threads or send 1-on-1 message |
| **Notifications** | `/api/notifications` | `GET` | Authenticated | Fetch user alerts & mark notifications as read |
| **Community** | `/api/community/posts` | `GET`, `POST` | Authenticated | View forum discussions or create post |
| **Chatbot** | `/api/chatbot/ask` | `POST` | Authenticated | Query Gemini AI farming assistant console |
| **Solar** | `/api/solar/calculate` | `POST` | Authenticated | Calculate solar panel wattage & pump HP |
| **Weather** | `/api/weather/advisory` | `GET` | Authenticated | Fetch localized 5-day weather & irrigation advice |
| **Admin** | `/api/admin/overview` | `GET` | Admin | Fetch system analytics & platform user counts |
| **Admin** | `/api/admin/crop-guides` | `POST`, `PUT` | Admin | Manage master crop database & stage compost |
| **Admin** | `/api/admin/notifications` | `POST` | Admin | Broadcast system-wide push alerts to farmers |

---

## 🛡️ Security & Best Practices

1. **Environment Configuration**: Secrets, JWT keys, and database passwords must **never** be checked into version control. Use `.env`.
2. **Password Hashing**: Uses `Werkzeug.security` with `pbkdf2:sha256` salted hashes.
3. **Role Guards**: Endpoints enforce role authorization using `@admin_required`, `@farmer_required`, or `@consumer_required` decorators.
4. **CORS Handling**: `Flask-CORS` configured with whitelist support for production frontend deployments (`Vercel`, `Netlify`, etc.).

---

## 🚀 Production Deployment

### Production Gunicorn Server
Run with 4 worker processes using `gunicorn`:
```bash
gunicorn --workers 4 --bind 0.0.0.0:5000 "run:app"
```

### Railway / Render Cloud Deployment
The repository includes a ready-to-use `railway.json` and `Procfile`:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn run:app`
- Set environment variables (`DATABASE_URL`, `JWT_SECRET_KEY`, `GEMINI_API_KEY`, `CORS_ORIGINS`) in your cloud dashboard.

---

## 📄 License & Credits

Developed for the **Valam (வளம்) Smart Agriculture Platform**. Built with Flask, SQLAlchemy, and Google Gemini AI.
