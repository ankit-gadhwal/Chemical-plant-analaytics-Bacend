import redis.asyncio as redis
from src.config import Config

JTI_EXPIRY = 3600

token_blocklist =  redis.from_url(Config.REDIS_URL,
    decode_responses=True)

async def add_jti_to_blocklist(jti: str) -> None:
    try:
        await token_blocklist.set(name=jti, value="", ex=JTI_EXPIRY)
    except Exception:
        pass

async def token_in_blocklist(jti: str) -> bool:
    try:
        val = await token_blocklist.get(jti)
        return val is not None
    except Exception:
        return False