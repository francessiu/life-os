import jwt
from jwt.algorithms import RSAAlgorithm
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.db.session import get_async_session
from backend.db.models import User, OAuthAccount
from backend.core.users import fastapi_users, get_user_manager
from backend.core.config import settings

router = APIRouter()

class AppleNativeLogin(BaseModel):
    id_token: str # The 'identityToken' string from ASAuthorizationAppleIDCredential
    first_name: str | None = None
    last_name: str | None = None

@router.post("/apple/native-login")
async def apple_native_login(
    payload: AppleNativeLogin,
    user_manager = Depends(get_user_manager),
    strategy = Depends(fastapi_users.get_auth_backend("jwt").get_strategy)
):
    """
    Verifies an Apple ID Token from iOS and issues a LifeOS JWT.
    """
    # 1. Fetch Apple's Public Keys
    apple_keys_url = "https://appleid.apple.com/auth/keys"
    async with httpx.AsyncClient() as client:
        resp = await client.get(apple_keys_url)
        keys = resp.json()["keys"]

    # 2. Decode the Header to find the Key ID (kid)
    header = jwt.get_unverified_header(payload.id_token)
    kid = header["kid"]
    
    # 3. Find the matching public key
    key_data = next((k for k in keys if k["kid"] == kid), None)
    if not key_data:
        raise HTTPException(status_code=400, detail="Invalid Apple Key ID")

    # 4. Verify Signature
    public_key = RSAAlgorithm.from_jwk(key_data)
    try:
        decoded = jwt.decode(
            payload.id_token, 
            public_key, 
            algorithms=["RS256"],
            audience=settings.APPLE_CLIENT_ID, # Your App Bundle ID here (e.g. com.lifeos.ios)
            issuer="https://appleid.apple.com"
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token expired")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Token: {str(e)}")

    # 5. Extract Email and ID
    email = decoded.get("email")
    apple_sub = decoded.get("sub") # The unique Apple User ID

    if not email:
        # Note: Apple ONLY sends email on the FIRST login. 
        # If it's missing, must rely on finding the user by 'apple_sub' in the OAuthAccount table.
        pass 

    # 6. Find or Create User (Logic simplified for brevity)
    # You would check your DB for a user with this email or this Apple 'sub'.
    # If they exist -> return login token.
    # If not -> create user -> return login token.
    
    # Example (Pseudo-code):
    # user = await user_manager.get_by_email(email)
    # token = await strategy.write_token(user)
    
    return {"access_token": "TODO_IMPLEMENT_USER_LOOKUP", "token_type": "bearer"}