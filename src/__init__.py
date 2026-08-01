from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.db.main import initdb
from src.datasets.routes import dataset_router
from src.Equipment.routes import equipment_router
from src.error import register_error_handlers
from .middleware import register_middleware
from .chatbot.routes import chat_router
from src.auth.router import auth_router
from src.documents.router import doc_router
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("Server is starting...")
#     await initdb()
#     yield
#     print("server is stoping")

app = FastAPI(
    title="Chemical Equipment Analytics API",
    # lifespan=lifespan  # add the lifespan event to our application
)
register_error_handlers(app)
register_middleware(app)
app.include_router(
    dataset_router,prefix="/dataset",
    tags=['dataset']
)
app.include_router(equipment_router,prefix="/equipment",tags=["Equipment"])
app.include_router(chat_router,prefix= "/chat",tags=["Chatbot"])
app.include_router(auth_router,prefix= "/auth",tags= ["Auth"])
app.include_router(doc_router,prefix= "/documents",tags= ["Documents"])