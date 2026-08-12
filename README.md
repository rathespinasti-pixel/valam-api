# Valam (வளம்) — Smart Agriculture API Backend

Flask + SQLAlchemy + JWT backend powering the Valam Smart Agriculture platform. Supports **Role-Based Portals (Farmer & Consumer)**, **Cloud Marketplace & Bargaining Engine**, **Direct 1-on-1 Chat**, **Pest & Disease Diagnosis**, **Crop Lifecycle Management**, **Irrigation & Solar Advisory**, and **Community Hub**.

---

## Folder Structure

```
valam-api/
├── app/
│   ├── __init__.py            # Application factory & blueprint registration
│   ├── config.py              # Environment configuration loader
│   ├── extensions.py          # SQLAlchemy, JWTManager, CORS instances
│   ├── models/
│   │   ├── user.py            # User model (Farmer & Consumer roles, profile fields)
│   │   ├── crop.py            # Farmer Crop tracker & 5-stage lifecycle state
│   │   ├── crop_guide.py      # Master agronomic crop guide dataset
│   │   ├── diagnosis.py       # Plant disease diagnosis reports
│   │   ├── marketplace_models.py # Produce listings, bargain offers, direct chat, notifications
│   │   ├── community.py       # Community forum posts and replies
│   │   ├── solar_guide.py     # Solar & irrigation guidelines
│   │   └── product.py         # Marketplace accessories & tools
│   ├── routes/
│   │   ├── auth.py            # Registration (Farmer/Consumer) & JWT login
│   │   ├── users.py           # User profiles & settings
│   │   ├── crops.py           # Crop tracking & stage transitions
│   │   ├── crop_guides.py     # Master guides & agronomic search
│   │   ├── diagnosis.py       # AI plant disease diagnosis endpoints
│   │   ├── cloud_market.py    # Cloud produce listings & bargaining negotiation
│   │   ├── direct_chat.py     # 1-on-1 direct messaging between users
│   │   ├── user_notifications.py # In-app notification center
│   │   ├── community.py       # Forum discussions & comments
│   │   ├── admin.py           # Administrative management & system audit
│   │   ├── chatbot.py         # AI farming assistant
│   │   ├── solar.py           # Solar irrigation guidance
│   │   └── weather.py         # Weather advisory endpoints
│   └── utils/
│       ├── decorators.py      # Auth and role-checking decorators
│       ├── ai_client.py       # Gemini AI client for crop & disease intelligence
│       └── weather_client.py  # Weather data provider wrapper
├── seed_admin.py              # Secure Administrator seeding utility
├── seed_vavuniya_data.py      # Northern Province crop guides & master seed data
├── run.py                     # Application startup & database table migrations
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
└── .gitignore                 # Version control ignore rules
```

---

## Quickstart & Setup

### 1. Prerequisites & Virtual Environment
```bash
python -m venv .venv
# On Windows PowerShell / Command Prompt:
.\.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment Configuration
Copy the template and configure your secrets:
```bash
cp .env.example .env
```
In `.env`, configure:
- `SECRET_KEY` & `JWT_SECRET_KEY`
- `DATABASE_URL` (Defaults to local SQLite if MySQL is unavailable)
- `ADMIN_EMAIL` & `ADMIN_PASSWORD` (For secure admin seeding)
- `GEMINI_API_KEY` (For AI agronomy and diagnosis)

### 3. Initialize & Seed Database
```bash
# Seed default agronomic guides and Vavuniya farming knowledge
python seed_vavuniya_data.py

# Securely seed the Super Admin account (reads from .env or CLI args)
python seed_admin.py
```

### 4. Run the API Server
```bash
python run.py
```
The API is available at `http://localhost:5000/api`.

---

## Security & Admin Seeding

- Admin credentials are **never hardcoded in source code**.
- Run `python seed_admin.py` to securely provision or update the administrator account using environment variables (`ADMIN_EMAIL`, `ADMIN_PASSWORD`) or CLI arguments:
  ```bash
  python seed_admin.py --email admin@valam.lk --password YourSecurePassword123! --name "Administrator"
  ```
