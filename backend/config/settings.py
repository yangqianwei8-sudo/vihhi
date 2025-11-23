import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-weihai-tech-production-system-2024')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Default allowed hosts includes Sealos deployment domain
DEFAULT_ALLOWED_HOSTS = 'localhost,127.0.0.1,tivpdkrxyioz.sealosbja.site'
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', DEFAULT_ALLOWED_HOSTS).split(',') if h.strip()]

# CSRF trusted origins (must include scheme)
# Default includes common Sealos deployment domains
DEFAULT_CSRF_ORIGINS = 'https://tivpdkrxyioz.sealosbja.site,http://tivpdkrxyioz.sealosbja.site,http://localhost:8001,http://127.0.0.1:8001,http://localhost:8000,http://127.0.0.1:8000'
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', DEFAULT_CSRF_ORIGINS).split(',') if o.strip()]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    'django_filters',
    
    # Local apps
    'backend.apps.permission_management.apps.PermissionManagementConfig',  # 必须在 system_management 之前
    'backend.apps.system_management.apps.SystemManagementConfig',
    'backend.apps.project_center',
    'backend.apps.customer_success.apps.CustomerSuccessConfig',
    'backend.apps.resource_standard',
    'backend.apps.task_collaboration',
    'backend.apps.production_quality.apps.ProductionQualityConfig',
    'backend.apps.delivery_customer',
    'backend.apps.settlement_center.apps.SettlementCenterConfig',
    'backend.apps.risk_management',
    # 行政管理模块
    'backend.apps.administrative_management.apps.AdministrativeManagementConfig',
    # 财务管理模块已禁用
    # 'backend.apps.financial_management.apps.FinancialManagementConfig',
    'backend.apps.personnel_management.apps.PersonnelManagementConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # Static files serving optimization in production
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.config.urls'

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

# Database configuration
# 优先使用环境变量 DATABASE_URL；若未配置，则使用最新的云端数据库连接
DEFAULT_DATABASE_URL = "postgresql://postgres:zdg7xx28@dbconn.sealosbja.site:38013/postgres"
database_url = os.getenv('DATABASE_URL', DEFAULT_DATABASE_URL).strip()
if database_url and "dbconn.sealosbja.site:45978" in database_url:
    database_url = database_url.replace("dbconn.sealosbja.site:45978", "dbconn.sealosbja.site:38013")

if database_url:
    # 使用生产环境数据库（如 PostgreSQL）
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # 开发环境使用 SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '25') or 25)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False') == 'True'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'noreply@example.com')

# 企业微信（WeCom）配置
WECOM_AGENT_ID = os.getenv('WECOM_AGENT_ID')
WECOM_CORP_ID = os.getenv('WECOM_CORP_ID')
WECOM_AGENT_SECRET = os.getenv('WECOM_AGENT_SECRET')
WECOM_DEFAULT_TO_USER = os.getenv('WECOM_DEFAULT_TO_USER', '')

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny' if DEBUG else 'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Whitenoise 配置 - 确保静态文件正确提供
WHITENOISE_USE_FINDERS = True  # 在开发模式下使用 finders
WHITENOISE_AUTOREFRESH = DEBUG  # 开发模式下自动刷新
WHITENOISE_MANIFEST_STRICT = False  # 允许静态文件即使不在 manifest 中也能访问
WHITENOISE_ROOT = STATIC_ROOT  # 明确指定 Whitenoise 的根目录

# 静态文件存储配置
# 在开发环境使用默认存储（无需 manifest）
# 在生产环境使用 Whitenoise 压缩存储，但需要确保 manifest 文件正确
if not DEBUG:
    try:
        # 生产环境：使用 Whitenoise 的压缩 manifest 存储
        STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    except ImportError:
        # 如果 Whitenoise 不可用，使用 Django 的 manifest 存储
        STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
else:
    # 开发环境：使用默认存储，避免 manifest 文件问题
    # 这样可以直接访问原始文件名（如 base.css），而不需要带哈希的文件名
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'system_management.User'

# Login settings
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# Cache: prefer Redis if REDIS_URL provided
REDIS_URL = os.getenv('REDIS_URL')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': os.getenv('CACHE_KEY_PREFIX', 'wh'),
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }

# Security settings for production
# Read from .env, but allow override for HTTP testing
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True' if not DEBUG else 'False') == 'True'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'True' if not DEBUG else 'False') == 'True'
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True' if not DEBUG else 'False') == 'True'
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
if not DEBUG:
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
