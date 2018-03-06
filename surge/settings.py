"""
Django settings for surge project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import djcelery
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

djcelery.setup_loader()
BROKER_URL = "amqp://surge:surgepasswd@localhost:5672/surge"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '&3u&b8+1a74_7hr!4o!bl)uvgo$n160tc9mta^8!-!-_aj6-5$'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'djcelery',
    'graphos',
    'surge',
    'asset',
    'operation',
    'rest_api',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'surge.middleware.AuthenticationMiddleware',
)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_api.authentication.APIKeyAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_api.authentication.IsOwnerResource',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter'
    ),
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
}

ROOT_URLCONF = 'surge.urls'

WSGI_APPLICATION = 'surge.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'surge',
        'USER': 'surge',
        'PASSWORD': 'surge',
        'HOST': '2.2.2.2',
        'PORT': 3306,
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

SESSION_MAX_AGE = 3 * 60 * 60  #3h
SESSION_SAVE_EVERY_REQUEST = True

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates/').replace('\\','/'),
)

STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

MEDIA_ROOT = 'upload/'
MEDIA_URL = 'upload/'


# User custom define
PAGE_SIZE = 30
MAX_PAGE_SIZE = 100

# Domain setting
DOMAIN = "http://1.1.1.1"

# Zabbix setting
ZABBIX_URL = 'http://zabbix.qq.com/'
ZABBIX_USER = ''
ZABBIX_PASSWORD = ''

# DNSPod setting
DNSPOD_URL = 'https://dnsapi.cn'
DNSPOD_USER = ''
DNSPOD_PASS = ''

# LOG setting
LOG_DIR = "/var/log/surge"
LOG_SIZE = "1024 * 1024 * 500" # 500M

if not os.path.isdir(LOG_DIR):
    os.makedirs(LOG_DIR)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s](%(levelname)s)%(name)s(%(lineno)s) : %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "default": {
            "level": "DEBUG",
            "filters": None,
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "surge.log"),
            "maxBytes": LOG_SIZE,
            "backupCount": 5,
            "formatter": "verbose"
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose"
        },
        "rabbitmq": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "surge-rabbitmq.log"),
            "maxBytes": LOG_SIZE,
            "backupCount": 5,
            "formatter": "verbose"
        },
        "zabbix": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "surge-zabbix.log"),
            "maxBytes": LOG_SIZE,
            "backupCount": 5,
            "formatter": "verbose"
        },
        "dnspod": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "surge-dnspod.log"),
            "maxBytes": LOG_SIZE,
            "backupCount": 5,
            "formatter": "verbose"
        }
    },
    "loggers": {
        "operation.endpoints": {
            "handlers": ["console", "rabbitmq"],
            "level": "DEBUG",
            "propagate": False
        },
        "asset.pyzabbix": {
            "handlers": ["console", "zabbix"],
            "level": "DEBUG",
            "propagate": False
        },
        "asset.dnspod": {
            "handlers": ["console", "dnspod"],
            "level": "DEBUG",
            "propagate": False
        },
        "operation": {
            "handlers": ["console", "default"],
            "level": "DEBUG",
            "propagate": False
        },
        "surge": {
            "handlers": ["console", "default"],
            "level": "DEBUG",
            "propagate": False
        },
        "asset": {
            "handlers": ["console", "default"],
            "level": "DEBUG",
            "propagate": False
        },
        "rest_api": {
            "handlers": ["console", "default"],
            "level": "DEBUG",
            "propagate": False
        },
    }
}
