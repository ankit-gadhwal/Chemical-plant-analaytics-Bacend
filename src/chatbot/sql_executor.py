from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from .logger import ChatLogger
from .metrics import Timer
from src.error import SQLExecutionFailed
from .schemas import ChatContext

class SQLExecutor:
    async def execute(self,sql: str,session:AsyncSession,context:ChatContext):

        timer = Timer()
        try:
            result = await session.execute(text(sql))
            rows = result.mappings().all()
            print(rows)
            ChatLogger.database_query(request_id=context.request_id,
                                      duration=timer.elapsed(),rows=len(rows))
            return rows

        except SQLAlchemyError as exc:
            raise SQLExecutionFailed(str(exc)) from exc
       