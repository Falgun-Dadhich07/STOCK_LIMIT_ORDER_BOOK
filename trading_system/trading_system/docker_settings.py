from .settings import *
import os

# Override Database Settings for Docker
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'trading_platform',
        'USER': 'trading_user',
        'PASSWORD': 'password',
        'HOST': 'db',  # Docker service name
        'PORT': '5432',
    }
}

# Override Channel Layers for Docker (Redis)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", 6379)],
        },
    },
}

# Allow all hosts in Docker
ALLOWED_HOSTS = ['*']

# Static files settings (if needed)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
