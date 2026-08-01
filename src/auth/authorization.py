from uuid import UUID

from fastapi import Depends

from .dependencies import AccessTokenBearer
from src.error import (AuthenticationFailed,UserNotVerified,UserInactive,
                       PermissionDenied,DatasetNotFound,EquipmentNotFound,AuthorizationError,NoDatasetAvailable)
from src.auth.service import UserService
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.models import Dataset,User,Equipment,UserRole
from src.datasets.service import DatasetService
from src.Equipment.service import EquipmentService

access_token = AccessTokenBearer()

user_service = UserService()

dataset_service = DatasetService()

equipment_service = EquipmentService()

async def get_current_user(
    token_data=Depends(access_token),
    session: AsyncSession = Depends(get_session),
):
    """
    Returns the authenticated user.
    """

    user_uid = UUID(token_data["user"]["user_uid"])

    user = await user_service.get_user_by_uid(
        user_uid=user_uid,
        session=session,
    )

    if user is None:
        raise AuthenticationFailed()

    return user



async def require_active_user(current_user: User =Depends(get_current_user)):
    """Ensures the authenticated user's account is active."""

    if not current_user.is_active:
        raise UserInactive()

    return current_user

async def require_verified_user(
    current_user: User=Depends(require_active_user),
):

    if not current_user.is_verified:
        raise UserNotVerified()

    return current_user

async def require_admin(current_user: User =Depends(require_verified_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise PermissionDenied(detail=
                               "You do not have permission to perform this action.")
    return current_user

async def require_dataset_owner(dataset_uid: UUID,
                               current_user: User =Depends(get_current_user),
                               session: AsyncSession = Depends(get_session)) -> Dataset:
    """
    Ensure that the authenticated user owns the requested dataset"""

    dataset = await dataset_service.get_dataset(dataset_uid=dataset_uid,session=session)

    if dataset is None:
        raise DatasetNotFound()

    if dataset.owner_uid != current_user.uid:
        raise PermissionDenied(
            detail="You are not authorized to access this dataset."
        )

    return dataset
    
async def require_dataset_access(dataset_uid: UUID,current_user: User,session: AsyncSession,):
    dataset_service = DatasetService()
    dataset = await dataset_service.get_dataset(dataset_uid=dataset_uid,
                                                session=session,)

    if dataset is None:
        raise NoDatasetAvailable()

    if current_user.role == UserRole.ADMIN:
        return dataset

    if dataset.owner_uid != current_user.uid:
        raise AuthorizationError()

async def require_equipment_owner(equipment_uid:UUID,current_usr:User = Depends(get_current_user),
                                  session:AsyncSession = Depends(get_session))  -> Equipment:
    """
    Ensure that the authenticated user owns the requested equipment"""

    equipment = await equipment_service.get_equipment_by_uid(current_usr.uid,equipment_uid,session)

    if equipment is None:
        raise EquipmentNotFound()

    return equipment

async def require_dataset_delete_permission(dataset_uid: UUID,current_user: User = Depends(get_current_user),
                                            session: AsyncSession = Depends(get_session)) -> Dataset:
    dataset = await dataset_service.get_dataset(dataset_uid, session)

    if dataset is None:
      raise DatasetNotFound()

    if current_user.role == UserRole.ADMIN:
      return dataset

    if dataset.owner_uid != current_user.uid:
      raise PermissionDenied()

    return dataset