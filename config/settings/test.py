import os

os.environ.setdefault("SECRET_KEY", "test-only-secret-key")
os.environ.setdefault("DATABASE_URL", "postgres://hsus:hsus@localhost:5432/hsus")

from .base import *  # noqa: E402, F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
