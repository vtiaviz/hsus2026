def normalize_username(request, credentials):
    """Usado pelo django-axes: tentativas de "Maria" e "maria" contam juntas."""
    return (credentials or {}).get("username", "").strip().lower()
