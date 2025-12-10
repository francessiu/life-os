from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from backend.core.config import settings

# 1. Transport: How the token is sent
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

# 2. Strategy: How the token is generated/validated
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.SECRET_KEY,
        lifetime_seconds=3600,  # Token valid for 1 hour
    )

# 3. Combine them into a Backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)