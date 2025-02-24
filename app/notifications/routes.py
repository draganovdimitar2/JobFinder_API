from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.main import get_session
from .service import NotificationService
from app.db.models import User
from app.auth.dependencies import RoleChecker, CustomTokenBearer

notification_router = APIRouter()
notification_service = NotificationService()
role_checker = RoleChecker(['USER', 'ORGANIZATION'])  # allowed roles


@notification_router.get("/notification")
async def get_all_notifications(current_user: User = Depends(role_checker),
                                session: AsyncSession = Depends(get_session)) -> list:
    """Get all notifications for a user. (including read ones)"""
    return await notification_service.get_all_notifications(str(current_user.uid), session)
