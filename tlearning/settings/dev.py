from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]
CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
SECRET_KEY = "dev-secret-key-do-not-use-in-prod"  # noqa: S105
