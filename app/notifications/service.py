from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.db.models import Notification
from app.db.models import User
from app.notifications.webhook import unread_notification_webhook as webhook


class NotificationService:
    async def trigger_notification(self, recipient_uid: str, sender_uid: str, message: str, session: AsyncSession):
        """Create a notification and trigger the webhook for unread count updates."""
        notification = Notification(
            recipient_uid=recipient_uid,
            sender_uid=sender_uid,
            message=message
        )
        session.add(notification)
        await session.commit()

        await webhook(recipient_uid, session)  # trigger the webhook to update the unread notification count

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

            notification = {
                "notification_id": str(notification.uid),
                "sender_name": sender_name,
                "message": notification.message + sender_name,  # add the current username
                "is_read": notification.is_read,
                "created_at": notification.created_at
            }
            notification_list.append(notification)

        return notification_list
