# backend/auth/oauth.py
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.clients.microsoft import MicrosoftGraphOAuth2
from backend.core.config import settings

# Google Client
google_oauth_client = GoogleOAuth2(
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
)

# Microsoft Client
microsoft_oauth_client = MicrosoftGraphOAuth2(
    client_id=settings.MICROSOFT_CLIENT_ID,
    client_secret=settings.MICROSOFT_CLIENT_SECRET,
)

# Note: Apple Auth requires a more complex setup with "sign_in_with_apple" lib
# usually handled better on the Frontend (Swift) sending an ID token to backend.