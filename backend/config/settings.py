import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-weihai-tech-production-system-2024')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Default allowed hosts includes Sealos deployment domain and server IP
DEFAULT_ALLOWED_HOSTS = 'localhost,127.0.0.1,10.107.164.84,tivpdkrxyioz.sealosbja.site,dbjhjowayeto.sealosbja.site,hrozezgtxwhk.sealosbja.site,wfnionzwqhsc.sealosbja.site,my-devbox.ns-dqyh88ke'
# Parse ALLOWED_HOSTS from environment variable, removing any wildcard entries
raw_hosts = [h.strip() for h in os.getenv('ALLOWED_HOSTS', DEFAULT_ALLOWED_HOSTS).split(',') if h.strip()]
# Filter out wildcard entries (Django doesn't support them directly)
ALLOWED_HOSTS = [h for h in raw_hosts if not h.startswith('*')]
# Note: Wildcard support for *.sealosbja.site is handled by AllowedHostsMiddleware

# CSRF trusted origins (must include scheme)
# Default includes common Sealos deployment domains and server IP
DEFAULT_CSRF_ORIGINS = 'https://tivpdkrxyioz.sealosbja.site,http://tivpdkrxyioz.sealosbja.site,https://dbjhjowayeto.sealosbja.site,http://dbjhjowayeto.sealosbja.site,https://hrozezgtxwhk.sealosbja.site,http://hrozezgtxwhk.sealosbja.site,https://wfnionzwqhsc.sealosbja.site,http://wfnionzwqhsc.sealosbja.site,http://localhost:8001,http://127.0.0.1:8001,http://10.107.164.84:8001,http://localhost:8000,http://127.0.0.1:8000'
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
    'backend.apps.customer_management.apps.CustomerManagementConfig',  # 客户管理（从customer_success迁移）
    'backend.apps.resource_standard',
    'backend.apps.settlement_management.apps.SettlementManagementConfig',  # 结算管理
    'backend.apps.settlement_center.apps.SettlementCenterConfig',  # 结算中心（仍被其他模块引用）
    'backend.apps.risk_management',
    # 行政管理模块
    'backend.apps.administrative_management.apps.AdministrativeManagementConfig',
    # 财务管理模块
    'backend.apps.financial_management.apps.FinancialManagementConfig',
    'backend.apps.personnel_management.apps.PersonnelManagementConfig',
    'backend.apps.workflow_engine.apps.WorkflowEngineConfig',
    # 交付客户模块（必须在 archive_management 之前，因为 archive_management 依赖它）
    'backend.apps.delivery_customer.apps.DeliveryCustomerConfig',
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
    # Static files serving optimization in production
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'backend.config.middleware.AllowedHostsMiddleware',  # 动态主机名验证（必须在 CommonMiddleware 之前）
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

# 移除 directConnection 参数（这是 MongoDB 的参数，PostgreSQL 不支持）
if database_url and "directConnection" in database_url:
    import re
    # 移除 directConnection 参数
    database_url = re.sub(r'[&?]directConnection=[^&]*', '', database_url)
    # 如果移除后 URL 以 & 结尾，清理掉
    database_url = database_url.rstrip('&')

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
# 授权信息来自：https://api.kuaidi100.com/manager/v2/myinfo/enterprise
# 企业：四川维海科技有限公司
KUAIDI100_CUSTOMER = os.getenv('KUAIDI100_CUSTOMER', '4E35F2EFE1EC0764032ED487AA4DC538')
KUAIDI100_KEY = os.getenv('KUAIDI100_KEY', 'MaOnMTzX7201')
# 其他参数（如需要）
KUAIDI100_SECRET = os.getenv('KUAIDI100_SECRET', '676d530653cb4505add04d911b826c53')
KUAIDI100_USERID = os.getenv('KUAIDI100_USERID', '56f5f07adbb746a28c76a25369907197')

# 企业微信（WeCom）配置
WECOM_AGENT_ID = os.getenv('WECOM_AGENT_ID')
WECOM_CORP_ID = os.getenv('WECOM_CORP_ID')
WECOM_AGENT_SECRET = os.getenv('WECOM_AGENT_SECRET')
WECOM_DEFAULT_TO_USER = os.getenv('WECOM_DEFAULT_TO_USER', '')

# 阿里云短信服务配置
# 阿里云短信服务文档：https://help.aliyun.com/product/44282.html
# 配置说明：
# 1. 访问阿里云控制台：https://dysms.console.aliyun.com/
# 2. 开通短信服务并获取 AccessKey ID 和 AccessKey Secret
# 3. 创建短信签名和短信模板
# 4. 配置以下参数
ALIYUN_SMS_ACCESS_KEY_ID = os.getenv('ALIYUN_SMS_ACCESS_KEY_ID', '')
ALIYUN_SMS_ACCESS_KEY_SECRET = os.getenv('ALIYUN_SMS_ACCESS_KEY_SECRET', '')
ALIYUN_SMS_SIGN_NAME = os.getenv('ALIYUN_SMS_SIGN_NAME', '维海科技')  # 短信签名
ALIYUN_SMS_TEMPLATE_CODE = os.getenv('ALIYUN_SMS_TEMPLATE_CODE', '')  # 短信模板代码（通用）
ALIYUN_SMS_REGISTER_TEMPLATE_CODE = os.getenv('ALIYUN_SMS_REGISTER_TEMPLATE_CODE', '')  # 注册验证码模板代码（如：SMS_500485017）
ALIYUN_SMS_REGION = os.getenv('ALIYUN_SMS_REGION', 'cn-hangzhou')  # 区域，默认杭州

# DeepSeek API配置（用于合同识别）
# DeepSeek API文档：https://platform.deepseek.com/api-docs/
# 需要在DeepSeek官网注册账号并获取API Key
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_API_BASE_URL = os.getenv('DEEPSEEK_API_BASE_URL', 'https://api.deepseek.com')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')  # 或 deepseek-v2

# ODA File Converter配置（用于DWG转DXF）
# 如果ODA File Converter不在系统PATH中，可以在这里指定完整路径
# Windows示例: r'C:\Program Files\ODA\ODAFileConverter 26.10.0\bin\DWGConvert.exe'
# Linux示例: '/opt/ODAFileConverter/bin/DWGConvert' 或 '/usr/local/bin/DWGConvert'
ODA_FILE_CONVERTER_PATH = os.getenv('ODA_FILE_CONVERTER_PATH', None)

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
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'  # 登录成功后重定向到首页
LOGOUT_REDIRECT_URL = '/login/'

# CSRF settings
CSRF_COOKIE_SECURE = False  # 开发环境设为False，生产环境应设为True（HTTPS）
CSRF_COOKIE_HTTPONLY = False  # 允许JavaScript访问CSRF token
CSRF_USE_SESSIONS = False  # 使用cookie存储CSRF token（默认）
CSRF_COOKIE_SAMESITE = 'Lax'  # 允许跨站请求

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
        'level': 'INFO',  # 开发环境使用INFO级别，减少DEBUG日志的I/O开销
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',  # 从DEBUG改为INFO，减少数据库查询日志
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',  # 数据库查询日志设置为WARNING，只在有问题时记录
            'propagate': False,
        },
        'django.template': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',  # 模板日志设置为WARNING，减少模板异常日志
            'propagate': False,
        },
        'django.utils.autoreload': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',  # 禁用autoreload的详细日志，减少文件监控日志输出
            'propagate': False,
        },
        'backend.config.admin': {
            'handlers': ['console', 'file'],
            'level': 'INFO',  # 从DEBUG改为INFO
            'propagate': False,
        },
    },
}
