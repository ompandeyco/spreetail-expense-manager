# Spreetail Expense Manager

A full-stack expense splitting application.

## Tech Stack

| Layer    | Technology                        |
|----------|-----------------------------------|
| Frontend | React + Vite + Tailwind CSS       |
| Backend  | Django REST Framework             |
| Auth     | JWT (SimpleJWT)                   |
| Database | PostgreSQL                        |

## Project Structure

```
spreetail-expense-manager/
├── backend/                  # Django project
│   ├── core/                 # Project config (settings, urls, wsgi)
│   ├── users/                # Custom user model + auth endpoints
│   ├── groups/               # Expense groups with members
│   ├── expenses/             # Expenses + splits
│   ├── importer/             # CSV bulk import
│   ├── settlements/          # Record debt payoffs
│   ├── .env                  # Environment variables (not committed)
│   ├── .env.example          # Template for .env
│   ├── requirements.txt      # Python dependencies
│   └── manage.py             # Django CLI
│
└── frontend/                 # React + Vite app
    ├── src/
    │   ├── context/          # React Context (AuthContext)
    │   ├── services/         # API layer (axios + auth functions)
    │   ├── components/       # Reusable components (ProtectedRoute)
    │   ├── pages/            # One file per page/route
    │   ├── App.jsx           # Route definitions
    │   └── main.jsx          # React entry point
    └── vite.config.js        # Vite + Tailwind config
```

## API Endpoints

| Method | URL                    | Description               | Auth?    |
|--------|------------------------|---------------------------|----------|
| POST   | /api/token/            | Get access + refresh token | No       |
| POST   | /api/token/refresh/    | Refresh access token       | No       |
| POST   | /api/users/register/   | Create account             | No       |
| GET    | /api/users/me/         | Get own profile            | Yes      |
| GET    | /api/groups/           | List groups                | Yes      |
| POST   | /api/groups/           | Create group               | Yes      |
| GET    | /api/expenses/         | List expenses              | Yes      |
| POST   | /api/expenses/         | Add expense                | Yes      |
| GET    | /api/importer/         | List import jobs           | Yes      |
| POST   | /api/importer/         | Upload CSV                 | Yes      |
| GET    | /api/settlements/      | List settlements           | Yes      |
| POST   | /api/settlements/      | Record settlement          | Yes      |

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # Edit DB credentials
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173
