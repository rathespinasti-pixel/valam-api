# Solar Farming Assistant — Backend API

Flask + MySQL + JWT backend implementing 6 modules: Auth, User Profiles,
AI Farming Chatbot, Solar Farming Guidance, Weather, and Marketplace.

## Folder Structure

```
farming_app_backend/
├── app/
│   ├── __init__.py            # App factory, blueprint registration
│   ├── config.py              # Env-based configuration
│   ├── extensions.py          # db, jwt, migrate, cors, swagger instances
│   ├── models/
│   │   ├── user.py            # User (auth + profile)
│   │   ├── chat.py            # ChatHistory (Module 3)
│   │   ├── solar_guide.py     # SolarGuide (Module 4)
│   │   ├── weather_subscription.py  # WeatherSubscription (Module 5)
│   │   └── product.py         # Product (Module 6)
│   ├── routes/
│   │   ├── auth.py            # Module 1
│   │   ├── users.py           # Module 2
│   │   ├── chatbot.py         # Module 3
│   │   ├── solar.py           # Module 4
│   │   ├── weather.py         # Module 5
│   │   └── products.py        # Module 6
│   └── utils/
│       ├── decorators.py      # response helpers, current-user helper
│       ├── ai_client.py       # AI provider wrapper (chatbot)
│       └── weather_client.py  # Weather provider wrapper
├── tests/
│   └── postman_collection.json
├── run.py                     # App entry point
├── seed.py                    # Sample data loader
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then edit .env with real values
```

Create the MySQL database:

```sql
CREATE DATABASE solar_farming_db CHARACTER SET utf8mb4;
```

Initialize and run migrations:

```bash
flask db init
flask db migrate -m "Initial tables"
flask db upgrade
```

(Optional) load sample data:

```bash
python seed.py
```

Run the app:

```bash
python run.py
# or
flask run
```

API base URL: `http://localhost:5000/api`
Swagger UI: `http://localhost:5000/apidocs/`

## Authentication

Most endpoints require a JWT bearer token obtained from
`/api/auth/login` or `/api/auth/register`:

```
Authorization: Bearer <access_token>
```

## Environment Variables (see `.env.example`)

- `DATABASE_URL` — MySQL connection string
- `SECRET_KEY`, `JWT_SECRET_KEY` — app/JWT signing secrets
- `AI_PROVIDER_API_KEY`, `AI_PROVIDER_URL` — chatbot AI provider (defaults to Anthropic Messages API format)
- `WEATHER_API_KEY`, `WEATHER_API_BASE_URL` — weather provider (defaults to OpenWeatherMap)
- `CORS_ORIGINS` — allowed frontend origin(s)

## API Testing

Import `tests/postman_collection.json` into Postman. Set the
`base_url` and `access_token` collection variables after logging in.

## Deployment

### Railway / Render
1. Push this repo to GitHub.
2. Create a new Web Service, connect the repo.
3. Set the environment variables from `.env.example` in the dashboard.
4. Add a managed MySQL database (Railway MySQL plugin, or Render's
   external MySQL/PlanetScale) and set `DATABASE_URL` accordingly.
5. Build command: `pip install -r requirements.txt`
6. Start command: `gunicorn run:app`
7. Run `flask db upgrade` once (via a one-off shell/job) to create tables.

### AWS (Elastic Beanstalk / EC2)
1. Provision an RDS MySQL instance; set `DATABASE_URL`.
2. Deploy the Flask app (Elastic Beanstalk Python platform, or EC2 +
   gunicorn + nginx).
3. Set environment variables via EB console or a `.env` on the instance.
4. Run migrations (`flask db upgrade`) as part of the deploy step.

## Notes

- Passwords are hashed with Werkzeug's `generate_password_hash`
  (PBKDF2-SHA256) — never stored in plain text.
- JWT logout is implemented via an in-memory token blocklist; for a
  multi-instance production deployment, replace `BLACKLISTED_TOKENS`
  in `app/extensions.py` with a shared store (e.g. Redis).
- `ask_ai_assistant()` in `app/utils/ai_client.py` defaults to the
  Anthropic Messages API format — swap the request body/headers if
  using a different provider (OpenAI, etc.).
