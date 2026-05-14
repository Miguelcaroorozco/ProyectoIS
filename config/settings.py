import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {'1', 'true', 'yes', 'on'}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default

SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-v$ef)a)spie+x-k#)yg5wwbz(@5rx&)(zf*_aza#(#n*@hb$5o',
)

DEBUG = os.getenv('DEBUG', '1').lower() in {'1', 'true', 'yes', 'on'}

DISABLE_PASSWORD_VALIDATORS = os.getenv('DISABLE_PASSWORD_VALIDATORS', '').lower() in {
    '1',
    'true',
    'yes',
    'on',
}

_allowed_hosts = os.getenv('ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts.split(',') if h.strip()] if _allowed_hosts else []


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core.importante',
    'core.administracion',
    'core.autenticacion',
    'apps.inicio',
    'apps.actividades',
    'apps.busqueda_avanzada',
    'apps.reportes',
    'apps.historial',
    'apps.generador_ia',
    'apps.configuracion',
    'core.administracion.gestion_usuarios',
    'core.usuarios',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.importante.context_processors.usuario_foto_contexto',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

_db_name = os.getenv('DB_NAME')

if _db_name:
    _db_charset = os.getenv('DB_OPTIONS_CHARSET', 'utf8mb4')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': _db_name,
            'USER': os.getenv('DB_USER', ''),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', '127.0.0.1'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': _db_charset,
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


if DEBUG or DISABLE_PASSWORD_VALIDATORS:
    AUTH_PASSWORD_VALIDATORS = []
else:
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]


LANGUAGE_CODE = 'es'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'core' / 'importante' / 'assets',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
LOGIN_URL = 'autenticacion:login'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'autenticacion:login'

_email_backend_env = os.getenv('EMAIL_BACKEND')
if _email_backend_env:
    EMAIL_BACKEND = _email_backend_env
else:
    # Auto-use SMTP when credentials are present; otherwise keep console backend.
    _smtp_host = os.getenv('EMAIL_HOST', '').strip()
    _smtp_user = os.getenv('EMAIL_HOST_USER', '').strip()
    _smtp_password = os.getenv('EMAIL_HOST_PASSWORD', '').strip()
    EMAIL_BACKEND = (
        'django.core.mail.backends.smtp.EmailBackend'
        if (_smtp_host and _smtp_user and _smtp_password)
        else 'django.core.mail.backends.console.EmailBackend'
    )
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@unitecnar.local')

# SMTP email settings (used when EMAIL_BACKEND is SMTP).
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = _env_int('EMAIL_PORT', 587)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# Typically use *either* TLS (587) or SSL (465).
EMAIL_USE_TLS = _env_bool('EMAIL_USE_TLS', default=True)
EMAIL_USE_SSL = _env_bool('EMAIL_USE_SSL', default=False)

EMAIL_TIMEOUT = _env_int('EMAIL_TIMEOUT', 20)
SERVER_EMAIL = os.getenv('SERVER_EMAIL', DEFAULT_FROM_EMAIL)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
