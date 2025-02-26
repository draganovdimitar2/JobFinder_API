from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.main import get_session
from .service import NotificationService
from app.db.models import User
from app.auth.dependencies import RoleChecker, CustomTokenBearer
from app.errors import NotificationNotFound, NotificationInsufficientPermission

notification_router = APIRouter()
notification_service = NotificationService()
role_checker = RoleChecker(['USER', 'ORGANIZATION'])  # allowed roles


@notification_router.get("/notification")
async def get_all_notifications(current_user: User = Depends(role_checker),
                                session: AsyncSession = Depends(get_session)):
    """Get all notifications for a user. (including read ones)"""
    return await notification_service.get_all_notifications(str(current_user.uid), session)


@notification_router.get("/notification/{notification_id}/details")
async def get_notification_details(notification_id: str,
                                   current_user: User = Depends(role_checker),
                                   session: AsyncSession = Depends(get_session)) -> dict:
    """Get notification details"""
    try:
        notification = await notification_service.get_notification_by_id(notification_id, session)
    except:
        raise NotificationNotFound()

    if str(notification.recipient) != str(current_user.uid):  # if user is trying to view other user's notifications
        raise NotificationInsufficientPermission()

    return await notification_service.get_notification_details(notification_id, session)
