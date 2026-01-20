import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-weihai-tech-production-system-2024')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Default allowed hosts - 生产环境只允许公网域名
# 重要：生产环境必须通过环境变量 ALLOWED_HOSTS 设置，只包含公网域名
# 当前配置的公网域名：
# - rasdmangrhdn.sealosbja.site (Port 8001, 可访问)
# - dbjhjowayeto.sealosbja.site (Port 8000, 准备中)
DEFAULT_ALLOWED_HOSTS = 'rasdmangrhdn.sealosbja.site,dbjhjowayeto.sealosbja.site'
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', DEFAULT_ALLOWED_HOSTS).split(',') if h.strip()]
# 开发环境：允许本地和测试客户端
if DEBUG:
    ALLOWED_HOSTS += ["127.0.0.1", "localhost", "testserver"]

# CSRF trusted origins (must include scheme)
# 生产环境只允许公网域名，开发环境允许本地访问
# 注意：生产环境应优先使用 HTTPS，HTTP 仅用于测试
DEFAULT_CSRF_ORIGINS = 'https://rasdmangrhdn.sealosbja.site,http://rasdmangrhdn.sealosbja.site,https://dbjhjowayeto.sealosbja.site,http://dbjhjowayeto.sealosbja.site'
if DEBUG:
    DEFAULT_CSRF_ORIGINS += ',http://localhost:8001,http://127.0.0.1:8001,http://localhost:8000,http://127.0.0.1:8000'
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', DEFAULT_CSRF_ORIGINS).split(',') if o.strip()]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',  # PostgreSQL支持，用于ArrayField等
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    'django_filters',
    
    # Local apps
    'backend.apps.permission_management.apps.PermissionManagementConfig',  # 必须在 system_management 之前
    'backend.apps.system_management.apps.SystemManagementConfig',
    'backend.apps.production_management.apps.ProductionManagementConfig',  # 生产管理（原项目中心）
    # 'backend.apps.project_center.apps.ProjectCenterConfig',  # 暂时保留：迁移文件依赖（临时注释：镜像中缺少此模块）
    'backend.apps.customer_management.apps.CustomerManagementConfig',  # 客户管理（从customer_success迁移）
    'backend.apps.resource_standard',
    'backend.apps.task_collaboration',
    'backend.apps.delivery_customer',
    'backend.apps.settlement_management.apps.SettlementManagementConfig',  # 结算管理
    'backend.apps.settlement_center.apps.SettlementCenterConfig',  # 结算中心（仍被其他模块引用）
    'backend.apps.risk_management',
    # 行政管理模块
    'backend.apps.administrative_management.apps.AdministrativeManagementConfig',
    # 财务管理模块
    'backend.apps.financial_management.apps.FinancialManagementConfig',
    'backend.apps.personnel_management.apps.PersonnelManagementConfig',
    'backend.apps.workflow_engine.apps.WorkflowEngineConfig',
    # 档案管理模块
    'backend.apps.archive_management.apps.ArchiveManagementConfig',
    # 诉讼管理模块
    'backend.apps.litigation_management.apps.LitigationManagementConfig',
    # 计划管理模块
    'backend.apps.plan_management.apps.PlanManagementConfig',
    # API接口管理模块
    'backend.apps.api_management.apps.ApiManagementConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # Host 守卫中间件 - 必须在 SecurityMiddleware 之后，严格验证 Host 头
    # 防止通过 Service IP、Pod IP、内部域名等方式绕过访问控制
    'backend.config.middleware.HostGuardMiddleware',
    # Static files serving optimization in production
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'backend.config.middleware.AutoLoginMiddleware',  # 自动登录中间件 - 已禁用，恢复登录页面
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
                'backend.core.context_processors.sidebar_menu',  # 自动提供当前模块的左侧菜单
                'backend.core.context_processors.notification_widget',  # 通知组件
                'backend.apps.system_management.context_processors.feedback_form',  # 反馈表单
            ],
        },
    },
]

# Database configuration
# 数据库配置说明：
# 1. 开发环境：使用环境变量 DATABASE_URL（如未设置，默认使用 Sealos 云端数据库）
# 2. 生产环境：必须设置 DATABASE_URL 环境变量指向本地数据库
# 3. 格式：postgresql://用户名:密码@主机:端口/数据库名

# 开发环境默认数据库（仅当 DATABASE_URL 未设置时使用）
# 注意：生产环境部署时，必须通过环境变量设置 DATABASE_URL，不要依赖此默认值
DEVELOPMENT_DATABASE_URL = os.getenv(
    'DEVELOPMENT_DATABASE_URL',
    "postgresql://postgres:zdg7xx28@dbconn.sealosbja.site:38013/postgres?directConnection=true"
)

# 优先使用 DATABASE_URL 环境变量
database_url = os.getenv('DATABASE_URL', '').strip()

# 如果未设置 DATABASE_URL，且为开发环境，使用开发默认数据库
if not database_url and DEBUG:
    database_url = DEVELOPMENT_DATABASE_URL.strip()

# 兼容旧配置：自动更新 Sealos 旧端口
if database_url and "dbconn.sealosbja.site:45978" in database_url:
    database_url = database_url.replace("dbconn.sealosbja.site:45978", "dbconn.sealosbja.site:38013")

# 仅对 Sealos 外网连接添加 directConnection 参数（本地数据库不需要）
if database_url and "dbconn.sealosbja.site" in database_url and "directConnection" not in database_url:
    separator = "&" if "?" in database_url else "?"
    database_url = f"{database_url}{separator}directConnection=true"

if database_url:
    # 使用 PostgreSQL 数据库
    import dj_database_url
    db_config = dj_database_url.config(
        default=database_url,
        conn_max_age=600,
        conn_health_checks=True,
    )
    # 修复 Python 3.13 与 psycopg2 的兼容性问题：禁用服务器端游标
    # 这可以解决 InvalidCursorName 错误（cursor does not exist）
    # DISABLE_SERVER_SIDE_CURSORS 是 Django PostgreSQL 后端的配置选项
    db_config['DISABLE_SERVER_SIDE_CURSORS'] = True
    DATABASES = {
        'default': db_config
    }
else:
    # 如果未配置数据库，使用 SQLite（仅用于本地开发测试）
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
# 公司对公邮箱：所有邮件必须通过此邮箱发送
COMPANY_EMAIL = 'whkj@vihgroup.com.cn'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', COMPANY_EMAIL)

# 快递查询API配置（快递100）
# 快递100 API文档：https://www.kuaidi100.com/openapi/api_post.shtml
# 需要在快递100官网注册账号并获取customer和key
KUAIDI100_CUSTOMER = os.getenv('KUAIDI100_CUSTOMER', '')
KUAIDI100_KEY = os.getenv('KUAIDI100_KEY', '')

# 企业微信（WeCom）配置
WECOM_AGENT_ID = os.getenv('WECOM_AGENT_ID')
WECOM_CORP_ID = os.getenv('WECOM_CORP_ID')
WECOM_AGENT_SECRET = os.getenv('WECOM_AGENT_SECRET')
WECOM_DEFAULT_TO_USER = os.getenv('WECOM_DEFAULT_TO_USER', '')

# DeepSeek API配置（用于合同识别）
# DeepSeek API文档：https://platform.deepseek.com/api-docs/
# 需要在DeepSeek官网注册账号并获取API Key
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_API_BASE_URL = os.getenv('DEEPSEEK_API_BASE_URL', 'https://api.deepseek.com')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')  # 或 deepseek-v2

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
# 开发环境允许本地访问
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# 生产环境：添加公网域名到 CORS 允许列表
if not DEBUG:
    CORS_ALLOWED_ORIGINS += [
        "https://rasdmangrhdn.sealosbja.site",
        "https://dbjhjowayeto.sealosbja.site",
    ]

CORS_ALLOW_CREDENTIALS = True

# Cache configuration
# 优先使用Redis缓存（如果可用），否则使用内存缓存
REDIS_URL = os.getenv('REDIS_URL', '')
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'weihai_tech',
            'TIMEOUT': 300,  # 默认5分钟过期
        }
    }
else:
    # 使用内存缓存作为后备方案
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
            'TIMEOUT': 300,  # 默认5分钟过期
            'OPTIONS': {
                'MAX_ENTRIES': 1000
            }
        }
    }

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
# 在生产环境中，WhiteNoise应该直接从STATIC_ROOT提供文件，不使用finders
WHITENOISE_USE_FINDERS = DEBUG  # 仅在开发模式下使用 finders
WHITENOISE_AUTOREFRESH = DEBUG  # 开发模式下自动刷新
WHITENOISE_MANIFEST_STRICT = False  # 允许静态文件即使不在 manifest 中也能访问
# 注意：不要设置WHITENOISE_ROOT，让WhiteNoise自动使用STATIC_ROOT

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

# Data upload limits
# 增加字段数量限制，解决 Django admin 页面字段过多时的 TooManyFieldsSent 错误
# 默认值为 1000，当模型有很多字段或 ManyToMany 关系时会超过此限制
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# Custom user model
AUTH_USER_MODEL = 'system_management.User'

# Login settings
# 使用自定义登录页面（/login/），而不是 Django Admin 登录页面
# 这样当用户未登录访问受保护页面时，会重定向到自定义登录页
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/login/'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/tmp/django_debug.log',
            'formatter': 'verbose',
            'mode': 'a',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'backend.config.admin': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
