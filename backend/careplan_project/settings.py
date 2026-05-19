import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'dev-secret-key-not-for-production'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'rest_framework',
    'corsheaders',
    'orders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'careplan_project.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'careplan'),
        'USER': os.environ.get('DB_USER', 'careplan_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'careplan_pass'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': '5432',
    }
}

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
USE_MOCK_LLM = os.environ.get('USE_MOCK_LLM', 'false').lower() == 'true'

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'UNAUTHENTICATED_USER': None,
    'EXCEPTION_HANDLER': 'orders.exception_handler.custom_exception_handler',
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
