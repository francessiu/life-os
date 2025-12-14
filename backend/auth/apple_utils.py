import jwt
import time
from backend.core.config import settings

def generate_apple_client_secret() -> str:
    """
    Generates a JWT signed with the .p8 private key.
    This acts as the 'client_secret' for Apple OAuth.
    """
    headers = {
        "kid": settings.APPLE_KEY_ID,
        "alg": "ES256" # Apple requires Elliptic Curve signature
    }

    payload = {
        "iss": settings.APPLE_TEAM_ID,
        "iat": int(time.time()),
        "exp": int(time.time()) + 15777000, # Valid for 6 months (max allowed)
        "aud": "https://appleid.apple.com",
        "sub": settings.APPLE_CLIENT_ID,
    }

    try:
        # Important: Ensure the private key string has standard PEM formatting
        # (-----BEGIN PRIVATE KEY----- ... -----END PRIVATE KEY-----)
        secret = jwt.encode(
            payload, 
            settings.APPLE_PRIVATE_KEY, 
            algorithm="ES256", 
            headers=headers
        )
        return secret
    except Exception as e:
        print(f"Error generating Apple Secret: {e}")
        return ""