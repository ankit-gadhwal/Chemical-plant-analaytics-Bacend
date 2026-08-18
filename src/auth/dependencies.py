from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from typing import Any
from fastapi import Depends,HTTPException,Request,status
from .utils import decode_token
from src.db.main import get_session
from src.db.models import User
from src.error import InvalidToken,RefreshTokenRequired,AccessTokenRequired
from src.db.redis import token_in_blocklist


class TokenBearer(HTTPBearer):

    """Dependency that extracts, validates, and decodes the JWT access token."""

    def __init__(self,auto_error:bool = True) -> None:
        super().__init__(auto_error=auto_error)

    async def __call__(self,request:Request) -> dict[str,Any]:
        # print("Authorization header:", request.headers.get("Authorization"))
        # print(dict(request.headers))
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        token = credentials.credentials
        payload = decode_token(token)

        if payload is None:
            raise InvalidToken()

        if await token_in_blocklist(payload.get('jti', '')):
            raise InvalidToken()

        self.verify_token_data(payload)

        return payload

    def token_valid(self, token: str) -> bool:
        token_data = decode_token(token)
        return token_data is not None 
    
    def verify_token_data(self,token_data):
        raise NotImplementedError("Please Override this method in child classes")
    
class AccessTokenBearer(TokenBearer):
    def verify_token_data(self,token_data: dict) -> None:
        if token_data and token_data['refresh']:
            raise AccessTokenRequired()

class RefreshTokenRequired(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=401,
            detail="Refresh token required."
        )       
        
class RefreshTokenBearer(TokenBearer):
    def verify_token_data(self,token_data: dict) ->None:
        if token_data and not token_data['refresh']:
            raise RefreshTokenRequired()
            