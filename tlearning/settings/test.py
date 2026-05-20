from .base import *  # noqa: F403

SECRET_KEY = "test-secret-key"  # noqa: S105
DATABASES["default"]["NAME"] = "tlearning_test"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # fast for tests
