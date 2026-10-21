from .base import *  # noqa: F403

DEBUG = True
# Para acessar por outro endereço (ex.: IP de uma VM), defina ALLOWED_HOSTS no .env.
ALLOWED_HOSTS = env.list(  # noqa: F405
    "ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "0.0.0.0"]
)
