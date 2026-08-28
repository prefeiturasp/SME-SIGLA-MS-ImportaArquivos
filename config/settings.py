"""Django settings for convocacao_processes project."""

import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DJANGO_ENVIRONMENT = os.environ.get("DJANGO_ENVIRONMENT", "local")
MS_PATH = os.environ.get("MS_PATH", "/ms-importa-arquivos")

BASE_DIR = Path(__file__).resolve().parent.parent
# Adiciona a pasta 'apps' ao sys.path do Python
sys.path.insert(0, os.path.join(BASE_DIR, "apps"))

SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-your-secret-key-here"
)
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "qa-api-sigla.sme.prefeitura.sp.gov.br",
    "hom-api-sigla.sme.prefeitura.sp.gov.br",
]
CSRF_TRUSTED_ORIGINS = [
    "https://qa-api-sigla.sme.prefeitura.sp.gov.br",
    "https://hom-api-sigla.sme.prefeitura.sp.gov.br",
]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "django_filters",
    "auditlog",
    "drf_spectacular",
    "core",
    "importa_arquivos",
    "exporta_arquivo",
]

MIDDLEWARE = [
    "sigla_sdk.middlewares.CorrelationIdMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "sigla_sdk.middlewares.AuditlogJWTMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

# Database
DB_ENGINE = os.environ.get("DB_ENGINE", "django.db.backends.postgresql")

if DB_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": os.environ.get("DB_NAME", BASE_DIR / "db.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": os.environ.get("DB_NAME", "db_sigla"),
            "USER": os.environ.get("DB_USER", "postgres"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "postgres"),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"  # noqa: E501
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.MinimumLengthValidator"  # noqa: E501
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.CommonPasswordValidator"  # noqa: E501
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.NumericPasswordValidator"  # noqa: E501
        ),
    },
]


# Internationalization
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

_ms_path_segment = (MS_PATH or "/ms-importa-arquivos").strip("/")
if DJANGO_ENVIRONMENT != "local":
    STATIC_URL = f"/{_ms_path_segment}/django_static/"
    MEDIA_URL = f"/{_ms_path_segment}/media/"
else:
    STATIC_URL = "/django_static/"
    MEDIA_URL = "/media/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ["Content-Disposition"]

SPECTACULAR_SETTINGS = {
    "TITLE": "Importa Arquivo Sigla API",
    "DESCRIPTION": "API para o sistema de importação de arquivos de sigla",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# DRF settings
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),
    "PAGE_SIZE": 10,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # "sigla_sdk.autenticacao.authentication.ApiKeyAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# AuditLog settings
AUDITLOG_INCLUDE_ALL_MODELS = False

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "sigla_sdk.logging.json_formatter.CustomJsonFormatter",
            "format": (
                "%(levelname)s %(asctime)s %(module)s %(filename)s %(lineno)d %(funcName)s %(message)s"  # noqa: E501
            ),
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "importa_arquivos": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "exporta_arquivo": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}


# SERVICES

CANDIDATOS_API_URL = os.environ.get(
    "CANDIDATOS_API_URL", "http://localhost:8000"
)
CANDIDATOS_API_TIMEOUT = int(os.environ.get("CANDIDATOS_API_TIMEOUT", 30))
CANDIDATOS_API_KEY = os.environ.get("CANDIDATOS_API_KEY", "api-key-candidatos")

CONCURSOS_API_URL = os.environ.get(
    "CONCURSOS_API_URL", "http://localhost:8001"
)
CONCURSOS_API_TIMEOUT = int(os.environ.get("CONCURSOS_API_TIMEOUT", 30))
CONCURSOS_API_KEY = os.environ.get("CONCURSOS_API_KEY", "api-key-concursos")

ESCOLHA_API_URL = os.environ.get("ESCOLHA_API_URL", "http://localhost:8004")
ESCOLHA_API_TIMEOUT = int(os.environ.get("ESCOLHA_API_TIMEOUT", 30))
ESCOLHA_API_KEY = os.environ.get("ESCOLHA_API_KEY", "api-key-escolha")

PROCESSOS_CONVOCACAO_API_URL = os.environ.get(
    "PROCESSOS_CONVOCACAO_API_URL", "http://localhost:8000"
)
PROCESSOS_CONVOCACAO_API_KEY = os.environ.get(
    "PROCESSOS_CONVOCACAO_API_KEY", "api-key-processos-convocacao"
)
PROCESSOS_CONVOCACAO_API_TIMEOUT = int(
    os.environ.get("PROCESSOS_CONVOCACAO_API_TIMEOUT", 30)
)

AGENDAS_API_URL = os.environ.get("AGENDAS_API_URL", "http://localhost:8007")
AGENDAS_API_KEY = os.environ.get("AGENDAS_API_KEY", "api-key-agenda")
AGENDAS_API_TIMEOUT = int(os.environ.get("AGENDAS_API_TIMEOUT", 30))

# API Key (autenticação entre microsserviços)
API_KEY = os.environ.get("API_KEY", "api-key-importa-arquivos")
API_KEY_HEADER = os.environ.get("API_KEY_HEADER", "X-API-Key")

JWT_SIGNING_KEY = os.environ.get(
    "JWT_SIGNING_KEY", os.environ.get("SECRET_KEY", "fallback-só-dev")
)

SIMPLE_JWT = {
    "SIGNING_KEY": JWT_SIGNING_KEY,
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=1440),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# PRODAM API Configuration
PRODAM_ESCOLHAS_API_URL = os.environ.get("PRODAM_ESCOLHAS_API_URL")
PRODAM_API_TOKEN = os.environ.get("PRODAM_API_TOKEN")
PRODAM_API_USUARIO = os.environ.get("PRODAM_API_USUARIO")
PRODAM_API_SENHA = os.environ.get("PRODAM_API_SENHA")

# Celery (broker, result backend e beat)
_celery_redis_url = os.environ.get("CELERY_REDIS_URL", "").strip()
CELERY_BROKER_URL = _celery_redis_url
CELERY_RESULT_BACKEND = _celery_redis_url
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
# A consulta PRODAM usa timeout de 300s; o limite da task precisa ser maior.
CELERY_TASK_SOFT_TIME_LIMIT = int(
    os.environ.get("CELERY_TASK_SOFT_TIME_LIMIT", 300)
)
CELERY_TASK_TIME_LIMIT = int(os.environ.get("CELERY_TASK_TIME_LIMIT", 360))
# Fila dedicada no Redis compartilhado (outros MS usam a fila "celery")
CELERY_TASK_DEFAULT_QUEUE = "importa_arquivos"

_beat_minutes = int(os.environ.get("IMPORTACAO_ESCOLHAS_BEAT_MINUTES", "1"))
CELERY_BEAT_SCHEDULE = {
    "enfileirar-importacao-escolhas": {
        "task": "importa_arquivos.tasks.enfileirar_importacoes_escolhas",
        "schedule": timedelta(minutes=_beat_minutes),
    },
}
