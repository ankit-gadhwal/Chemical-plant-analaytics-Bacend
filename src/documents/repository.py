import uuid

from sqlalchemy import desc
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.models import Document


class DocumentRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        document: Document,
    ) -> Document:

        self.session.add(document)

        await self.session.commit()

        await self.session.refresh(document)

        return document

    async def get_by_uid(
        self,
        document_uid: uuid.UUID,
    ) -> Document | None:

        statement = (
            select(Document)
            .where(Document.uid == document_uid)
        )

        result = await self.session.exec(statement)

        return result.first()

    async def get_by_dataset(
        self,
        dataset_uid: uuid.UUID,
    ) -> list[Document]:

        statement = (
            select(Document)
            .where(Document.dataset_uid == dataset_uid)
            .order_by(desc(Document.created_at))
        )

        result = await self.session.exec(statement)

        return result.all()

    async def delete(
        self,
        document: Document,
    ) -> None:

        await self.session.delete(document)

        await self.session.commit()