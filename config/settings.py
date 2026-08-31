import os
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega variáveis de ambiente do arquivo .env se existir
env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(env_path)

# OngSys API v2 Settings
ONGSYS_USERNAME = os.getenv('ONGSYS_USERNAME', os.getenv('ONGSYS_CNPJ', ''))
ONGSYS_PASSWORD = os.getenv('ONGSYS_PASSWORD', os.getenv('ONGSYS_API_KEY', ''))
ONGSYS_URL_BASE = os.getenv(
    'ONGSYS_URL_BASE',
    os.getenv('ONGSYS_BASE_URL', 'https://www.ongsys.com.br/app/index.php/api/v2/'),
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-u(fyrn(z%fhd1w*jgu(3y5w^5hf_e=l9n#(vi)q*gvbj))88-o')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

allowed_hosts_env = os.getenv('ALLOWED_HOSTS', 'core.cdc.org.br,*.cdc.org.br,localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_env.split(',') if h.strip()] if not DEBUG else ['*']

CSRF_TRUSTED_ORIGINS = [
    'https://core.cdc.org.br',
    'https://*.cdc.org.br',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# SECURITY HEADERS FOR LGPD & DATA PROTECTION
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() in ('true', '1', 't')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Core Apps
    'apps.dashboard.apps.DashboardConfig',
    'apps.dataops.apps.DataopsConfig',
    'apps.integrations.apps.IntegrationsConfig',
]

# Integrações M2M de saída. Segredos são lidos somente no servidor e nunca
# enviados a templates, respostas HTTP ou logs.
NEXTERP_BASE_URL = os.getenv('NEXTERP_BASE_URL', '').rstrip('/')
NEXTERP_API_KEY = os.getenv('NEXTERP_API_KEY', '')
NEXTERP_API_SECRET = os.getenv('NEXTERP_API_SECRET', '')
NEXTERP_CONNECT_TIMEOUT = float(os.getenv('NEXTERP_CONNECT_TIMEOUT', '5'))
NEXTERP_READ_TIMEOUT = float(os.getenv('NEXTERP_READ_TIMEOUT', '30'))
NEXTERP_MAX_RETRIES = int(os.getenv('NEXTERP_MAX_RETRIES', '3'))

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases


def database_config(database_url):
    """Converte DATABASE_URL em configuração Django sem dependência adicional."""
    if not database_url:
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }

    parsed = urlparse(database_url)
    if parsed.scheme not in ('postgres', 'postgresql'):
        raise ImproperlyConfigured(
            'DATABASE_URL deve usar o esquema postgres:// ou postgresql://.'
        )
    if not all((parsed.hostname, parsed.path.lstrip('/'), parsed.username)):
        raise ImproperlyConfigured('DATABASE_URL do PostgreSQL está incompleta.')

    config = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': unquote(parsed.path.lstrip('/')),
        'USER': unquote(parsed.username),
        'PASSWORD': unquote(parsed.password or ''),
        'HOST': parsed.hostname,
        'PORT': str(parsed.port or 5432),
        'CONN_MAX_AGE': int(os.getenv('DATABASE_CONN_MAX_AGE', '60')),
        'CONN_HEALTH_CHECKS': True,
    }
    options = dict(parse_qsl(parsed.query, keep_blank_values=False))
    if options:
        config['OPTIONS'] = options
    return config


DATABASES = {'default': database_config(os.getenv('DATABASE_URL', '').strip())}

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
