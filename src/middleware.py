import time
from fastapi import FastAPI,Request
from src.logger import logger
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

def register_middleware(app:FastAPI):
    @app.middleware("http")
    async def custom_logging(request: Request,call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(f"{request.method} {request.url.path}")
            raise
        elapsed = (time.perf_counter() - start) * 1000

        logger.info(
            "%s %s %s %s %d %.2f ms",request.client.host,request.client.port,request.method,request.url.path,response.status_code,elapsed)
        return response
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost","127.0.0.1"],
    )
