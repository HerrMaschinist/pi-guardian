import secrets


def generate_api_key() -> str:
    """Generiert einen eindeutigen API-Key mit erkennbarem PI-Guardian-Präfix."""
    return f"pig_{secrets.token_urlsafe(32)}"
