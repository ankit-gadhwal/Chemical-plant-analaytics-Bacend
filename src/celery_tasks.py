from celery import Celery
from asgiref.sync import async_to_sync
from src.datasets.service import DatasetService
from src.db.main import AsyncSessionLocal
from src.config import Config
from src.celery_app import c_app
import uuid
import asyncio
from asyncpg.exceptions import ConnectionDoesNotExistError
from sqlalchemy.exc import OperationalError
from src.mail import mail,create_message

# c_app.config_from_object("src.config")  #it also work but for better use i am using config.update
# c_app.conf.update(
#     broker_url=Config.REDIS_URL,
#     result_backend=Config.REDIS_URL,
#     task_serializer="json",
#     result_serializer="json",
#     accept_content=["json"],
#     timezone="Asia/Kolkata",
#     enable_utc=False,
# )
@c_app.task(
    autoretry_for=(OperationalError,ConnectionDoesNotExistError,),
    retry_backoff=True,retry_backoff_max=60,retry_jitter=True,retry_kwargs={"max_retries": 3})

def process_dataset(dataset_uid: uuid.UUID):
    asyncio.run((process_dataset_async(dataset_uid)))

async def process_dataset_async(dataset_uid: uuid.UUID):
    service = DatasetService()
    async with AsyncSessionLocal() as session:
        await service.process_dataset(dataset_uid = dataset_uid,
                                      session=session)


from src.mail import send_email_async

@c_app.task()
def send_email(recipients: list[str], subject: str, body: str):
    print("Inside send_email task")
    try:
        async_to_sync(send_email_async)(recipients, subject, body)
        print("Email task executed successfully")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(e)