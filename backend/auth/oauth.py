from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.clients.microsoft import MicrosoftGraphOAuth2
from httpx_oauth.clients.apple import AppleOAuth2 # Built-in client

from backend.core.config import settings
from backend.auth.apple_utils import generate_apple_client_secret

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

# Apple Client
# Generate the secret on startup. 
# In a long-running production app, regenerate this. 
apple_oauth_client = AppleOAuth2(
    client_id=settings.APPLE_CLIENT_ID,
    client_secret=generate_apple_client_secret(),
)