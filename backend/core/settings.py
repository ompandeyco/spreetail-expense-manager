"""
Django settings for spreetail-expense-manager backend.

Reads sensitive values from environment variables via python-dotenv.
"""

import os
import dj_database_url
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Load .env file so we don't hard-code secrets
load_dotenv()

# ─── Base directory ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent


# ─── Security ────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me-in-production")

DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")


# ─── Installed apps ──────────────────────────────────────────────────────────
INSTALLED_APPS = [
    # Django built-in apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party packages
    "rest_framework",           # Django REST Framework
    "rest_framework_simplejwt", # JWT authentication
    "corsheaders",              # Allow React frontend to talk to this API

    # Our custom apps
    "users",
    "groups",
    "expenses",
    "importer",
    "settlements",
]


# ─── Middleware ───────────────────────────────────────────────────────────────
MIDDLEWARE = [
    # CORS middleware must be at the top so it runs first
    "corsheaders.middleware.CorsMiddleware",

    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ─── URL configuration ────────────────────────────────────────────────────────
ROOT_URLCONF = "core.urls"


# ─── Templates ───────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ─── WSGI ─────────────────────────────────────────────────────────────────────
WSGI_APPLICATION = "core.wsgi.application"


# ─── Database (PostgreSQL) ────────────────────────────────────────────────────
# Production (Render): DATABASE_URL env var is set automatically by Render.
# Local dev:           Individual DB_* env vars loaded from .env.
_DATABASE_URL = os.getenv("DATABASE_URL")

if _DATABASE_URL:
    # ── Production / Render ──────────────────────────────────────────────────
    # dj_database_url parses the full connection string into a Django DATABASES
    # dict.  conn_max_age=600 keeps connections alive for 10 minutes (recommended
    # for Render's managed Postgres).  ssl_require=True enforces TLS.
    DATABASES = {
        "default": dj_database_url.config(
            default=_DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    # ── Local development ────────────────────────────────────────────────────
    # Falls back to individual env vars defined in .env (DB_NAME, DB_USER, etc.)
    DATABASES = {
        "default": {
            "ENGINE":   "django.db.backends.postgresql",
            "NAME":     os.getenv("DB_NAME", "spreetail_db"),
            "USER":     os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
            "HOST":     os.getenv("DB_HOST", "localhost"),
            "PORT":     os.getenv("DB_PORT", "5432"),
        }
    }


# ─── Password validation ──────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ─── Internationalisation ─────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ─── Static files ─────────────────────────────────────────────────────────────
STATIC_URL = "static/"


# ─── Default primary key ─────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ─── Custom User Model ────────────────────────────────────────────────────────
# We tell Django to use our own User model instead of the default one
AUTH_USER_MODEL = "users.User"


# ─── Django REST Framework ────────────────────────────────────────────────────
REST_FRAMEWORK = {
    # Every API endpoint requires a valid JWT token by default
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}


# ─── JWT settings (SimpleJWT) ─────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(minutes=60),   # Access token valid for 1 hour
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),       # Refresh token valid for 7 days
    "ROTATE_REFRESH_TOKENS":  True,                    # Issue new refresh token on every refresh
    "AUTH_HEADER_TYPES":      ("Bearer",),             # Expect: Authorization: Bearer <token>
}


# ─── CORS (Cross-Origin Resource Sharing) ────────────────────────────────────
# Allow the React dev server to make requests to this Django API
cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS")
if cors_origins_env:
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins_env.split(",")]
else:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:5173",   # Vite default dev port
        "http://localhost:3000",
    ]


STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"