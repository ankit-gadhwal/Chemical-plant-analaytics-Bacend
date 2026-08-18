from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession
import uuid
from src.auth.authorization import get_current_user
from src.db.main import get_session
from .schemas import DocumentResponse
from .service import DocumentService
from src.db.models import User
from fastapi.exceptions import HTTPException

doc_router = APIRouter()


@doc_router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    dataset_uid: uuid.UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),):
    service = DocumentService(session)
    return await service.upload_document(
        dataset_uid=dataset_uid,
        file=file,
        current_user=current_user,
    )

@doc_router.get("/dataset/{dataset_uid}",
    response_model=list[DocumentResponse],)
async def get_documents_by_dataset(
    dataset_uid: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):

    service = DocumentService(session)
    res = await service.get_documents_by_dataset(
        dataset_uid,
        current_user,
    )
        
    return res


@doc_router.get("/{document_uid}",response_model=DocumentResponse,)

async def get_document(document_uid: uuid.UUID,
    session: AsyncSession = Depends(get_session),current_user: User = Depends(get_current_user)):

    service = DocumentService(session)
    return await service.get_document(
        document_uid,current_user)


@doc_router.delete("/{document_uid}",status_code=status.HTTP_200_OK)


async def delete_document(
    document_uid: uuid.UUID,session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)):

    service = DocumentService(session)

    return await service.delete_document(
        document_uid,
        current_user,
    )