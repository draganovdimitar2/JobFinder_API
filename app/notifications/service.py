from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.db.models import Notification
from app.db.models import User
from app.notifications.webhook import unread_notification_webhook as webhook
from typing import Optional
from sqlalchemy.sql.expression import or_, and_
from datetime import datetime
import uuid


class NotificationService:
    async def trigger_notification(
            self,
            recipient_uid: uuid.UUID,
            sender_uid: uuid.UUID,
            message: str,
            session: AsyncSession,
            job_id: Optional[uuid.UUID] = None,
            # if job_like is given we add job_id to db, so we can fetch the job later
            application_id: Optional[uuid.UUID] = None  # if application status is changed, we add application_id to db
    ):
        """Create a notification and trigger the webhook for unread count updates."""
        # Check if a notification already exists
        statement = select(Notification).where(
            and_(
                Notification.recipient_uid == recipient_uid,
                Notification.sender_uid == sender_uid,
                or_(
                    Notification.application_id == application_id,
                    Notification.job_id == job_id
                )
            )
        )
        result = await session.execute(statement)
        existing_notification = result.scalars().first()

        if existing_notification:
            # Update the existing notification
            existing_notification.message = message  # Update the message with the latest status
            existing_notification.created_at = datetime.utcnow()  # Update timestamp
        else:
            # Create a new notification if none exists
            notification = Notification(
                recipient_uid=recipient_uid,
                sender_uid=sender_uid,
                message=message,
                job_id=job_id,
                application_id=application_id
            )
            session.add(notification)

        await session.commit()

        await webhook(str(recipient_uid), session)  # Trigger webhook to update unread count

    async def get_all_notifications(self, user_uid: str, session: AsyncSession) -> list:
        """Fetch all notification."""

        statement = select(Notification).where(Notification.recipient_uid == user_uid)
        result = await session.exec(statement)
        all_notifications = result.all()

        notification_list = []
        for notification in all_notifications:
            # statement to fetch the notification sender username
            statement = select(User.username).where(User.uid == str(notification.sender_uid))
            result = await session.execute(statement)
            sender_name = result.scalars().first()
            if notification.job_id is not None:  # ensure that concatenation will be made for the right notification
                notification.message += sender_name  # add the current username (in case user has changed it)

            notification = {
                "notification_id": str(notification.uid),
                "sender_name": sender_name,
                "message": notification.message,
                "is_read": notification.is_read,
                "created_at": notification.created_at
            }
            notification_list.append(notification)

        return notification_list

    async def get_notification_by_id(self, notification_id: str, session: AsyncSession) -> dict:
        """Fetch notification by its id."""
        statement = select(Notification).where(Notification.uid == notification_id)
        result = await session.execute(statement)
        notification = result.scalars().first()
        return notification

    async def check_notification_existence(
            self,
            credentials: str,
            recipient_uid: uuid.UUID,
            sender_uid: uuid.UUID,
            session: AsyncSession
    ) -> bool:
        """Return boolean value based on whether notification exists"""
        statement = select(Notification).where(
            and_(
                # check whether application_id or job_id are the same, and whether recipient_uid and sender_uid are the same.
                or_(Notification.application_id == credentials, Notification.job_id == credentials),
                Notification.recipient_uid == recipient_uid,
                Notification.sender_uid == sender_uid
            )
        )
        result = await session.execute(statement)
        notification = result.first()
        return bool(notification)  # Return True if a notification exists, else False
