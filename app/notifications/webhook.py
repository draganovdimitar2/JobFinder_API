import httpx
from sqlmodel import select
from app.db.models import Notification
from sqlmodel.ext.asyncio.session import AsyncSession

WEBHOOK_URL = "https://webhook.site/52d40ef4-0032-4275-ba61-de2500bd8464"  # url to the main page where push notifications will show


async def unread_notification_webhook(user_uid: str, session: AsyncSession):
    """Send an unread notification count update to the frontend."""
    query = select(Notification).where(Notification.recipient_uid == user_uid, Notification.is_read == False)
    result = await session.execute(query)
    count = len(result.scalars().all())

    async with httpx.AsyncClient() as client:
        try:
            await client.post(WEBHOOK_URL, json={"user_uid": user_uid, "unread_count": count})
        except Exception as e:
            print(f"Failed to send webhook: {e}")

"""
{
  "user_uid": "91d64cda-3e95-4972-ae97-8c757be48d1c",  # recipient_id
  "unread_count": 1  # his unread notifications
}
"""