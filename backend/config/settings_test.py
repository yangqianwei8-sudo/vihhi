"""
测试环境配置
用于运行单元测试和验收测试，最小化外部依赖
"""
from .settings import *  # noqa

# 测试环境配置
DEBUG = False

# 测试环境必须允许 testserver，否则 Django test client 会 DisallowedHost
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

# 使用本地内存缓存，避免依赖 Redis/外部缓存服务
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

# 使用内存邮件后端，避免真实发信
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# 禁用日志文件写入（测试环境不需要）
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",  # 测试环境减少日志输出
    },
}

# 测试数据库配置：使用 SQLite 内存数据库（最快，无需清理）
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
