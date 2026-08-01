from passlib.context import CryptContext
from datetime import datetime,timedelta,UTC
import jwt
import uuid
from src.config import Config
import logging
from itsdangerous import URLSafeTimedSerializer

passwd_context = CryptContext(schemes=['bcrypt'])

def generate_password_hash(password: str) -> str:
    hash_password = passwd_context.hash(password)
    return hash_password

def verify_password(password: str,hash_password: str) -> bool:
    return passwd_context.verify(password,hash_password)

def create_access_token(user_data: dict,expiry: timedelta=None,refresh: bool=False)->str:

    payload = {
        'user':user_data,
        'exp' : datetime.now(UTC) + (expiry if expiry is not None else timedelta(minutes=60)),
        'jti' : str(uuid.uuid4()),
        'refresh': refresh
    }

    token = jwt.encode(payload=payload,
                       key=Config.JWT_SECRET,
                       algorithm=Config.JWT_ALGORITHM)

    return token

def decode_token(token : str) -> dict:
    try:
        token_data = jwt.decode(
        jwt=token,
        key=Config.JWT_SECRET,
        algorithms=[Config.JWT_ALGORITHM]
        )
        return token_data

    except jwt.PyJWTError as jwte:
        logging.exception(jwte)
        return None

    except Exception as e:
        logging.exception(e)
        return None

serializer = URLSafeTimedSerializer(
    secret_key=Config.JWT_SECRET,salt="email-configuration"
)

def create_url_safe_token(data: dict):
    """Serialize a dict into a URLSafe token"""

    token = serializer.dumps(data)

    return token

def decode_url_safe_token(token:str):
    """Deserialize a URLSafe token to get data"""
    try:
        token_data = serializer.loads(token)

        return token_data
    
    except Exception as e:
        logging.error(str(e))  