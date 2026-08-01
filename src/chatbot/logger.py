import logging
from uuid import UUID

logger = logging.getLogger("chatbot")

class ChatLogger:

    @staticmethod
    def question(request_id: str,dataset_uid: UUID,question: str):
        logger.info("[%s] Question | Dataset=%s",request_id,dataset_uid,question)

    @staticmethod
    def dataset_validated(request_id: str,dataset_uid: UUID):
        logger.info("[%s] Dataset validated | %s",request_id,dataset_uid)

    @staticmethod
    def generated_sql(request_id: str,sql: str,duration: float):
        logger.info("[%s] SQL generated in %.3fs\n%s",request_id,duration,sql)

    @staticmethod
    def answer_generated(requested_id: str,duration: float):
        logger.info("[%s] Answer generated in %.3fs",requested_id,duration)

    @staticmethod
    def requested_completed(request_id:str,total_time: float):
        logger.info("[%s] Request completed in %.3fs",request_id,total_time)

    @staticmethod
    def error(request_id : str,exc: Exception):
        logger.exception("[%s] %s",request_id,str(exc))

    @staticmethod
    def database_query(request_id: str,duration: float,rows: int):
        logger.info("[%s] Database query in %.3fs | Rows=%d",request_id,duration,rows)
    