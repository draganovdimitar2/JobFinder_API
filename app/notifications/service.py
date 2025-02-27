from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.db.models import Notification
from app.db.models import User, Applications
from app.notifications.webhook import unread_notification_webhook as webhook
from typing import Optional
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
        if "was liked by" in message:  # if notification is related to job_likes
            statement = select(Notification).where(
                # we don't check for application_id because it is not present
                Notification.recipient_uid == recipient_uid,
                Notification.sender_uid == sender_uid,
                Notification.message == message,
                Notification.job_id == job_id
            )
        else:  # if notification is related to application_status
            statement = select(Notification).where(
                # here we only check for application_id because we don't have job_id
                Notification.recipient_uid == recipient_uid,
                Notification.sender_uid == sender_uid,
                Notification.application_id == application_id
            )

        result = await session.execute(statement)
        existing_notification = result.scalars().first()

        if existing_notification:
            # update the existing notification
            existing_notification.message = message  # update the message with the latest status
            existing_notification.created_at = datetime.utcnow()  # update timestamp
        else:
            # create a new notification if none exists
            notification = Notification(
                recipient_uid=recipient_uid,
                sender_uid=sender_uid,
                message=message,
                job_id=job_id,
                application_id=application_id

            )
            session.add(notification)

        await session.commit()

        await webhook(str(recipient_uid), session)  # trigger webhook to update unread count

    async def get_all_notifications(self, user_uid: str, session: AsyncSession):
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
            if notification.job_id is not None and 'new applicant' not in notification.message:  # ensure that concatenation will be made for the right notification
                notification.message += sender_name  # add the current username (in case user has changed it)

            notification = {
                "notification_id": str(notification.uid),
                "sender_name": sender_name,
                "message": notification.message,
                "is_read": notification.is_read,
                "created_at": notification.created_at,
                "job_id": str(notification.job_id) if notification.job_id else None,
                "application_id": str(notification.application_id) if notification.application_id else None
            }
            notification_list.append(notification)

        if not notification_list:  # if notifications are empty
            return {"message": "You don't have notifications yet"}
        return notification_list

    async def get_notification_by_id(self, notification_id: str, session: AsyncSession) -> dict:
        """Fetch notification by its id."""
        statement = select(Notification).where(Notification.uid == notification_id)
        result = await session.execute(statement)
        notification = result.scalars().first()
        return notification

    async def get_notification_details(self, notification_id: str, session: AsyncSession) -> dict:
        """Fetch job and application details based on notification_id"""

        from app.jobs.service import JobService
        job_service = JobService()

        notification = await self.get_notification_by_id(notification_id, session)
        if not notification:
            return {"message": "Notification not found!"}

        # Set notification is_read to True
        notification.is_read = True
        session.add(notification)
        await session.commit()

        if notification.job_id is not None:  # return job details
            job = await job_service.get_job_data(str(notification.job_id), session)
            if not job:  # if unable to fetch the job
                return {"message": "Job is deleted or inactive!"}
            else:
                job_dict = {
                    "_id": str(job.uid),
                    "title": job.title,
                    "description": job.description,
                    "type": job.type,
                    "likes": job.likes,
                    "category": job.category,
                    "author_uid": str(job.author_uid),
                    "isActive": job.is_active
                }
                if "new applicant" in notification.message:  # if notification is for new applicant, we add application details in job_dict
                    statement = select(Applications).where(Applications.job_uid == job_dict['_id'],
                                                           Applications.user_uid == notification.sender_uid)
                    result = await session.exec(statement)
                    application = result.first()
                    statement = select(User).where(Applications.user_uid == User.uid)
                    result = await session.exec(statement)
                    user = result.first()
                    job_dict['applicationCoverLetter'] = application.coverLetter
                    job_dict['application_status'] = application.status
                    job_dict['appliedAt'] = application.appliedAt
                    job_dict['applicantUsername'] = user.username
                return job_dict
        # If it's not a job like notification, fetch application details + job details
        statement = select(Applications).where(Applications.uid == notification.application_id)
        result = await session.exec(statement)
        application = result.first()  # fetch the application
        if not application:
            return {"message": "Application not found or deleted!"}

        job = await job_service.get_job_data(application.job_uid, session)
        if not job:  # if job is not found
            return {"message": "Job is deleted or inactive!"}
        else:
            isLiked = await job_service.like_checker(str(application.user_uid), str(job.uid), session)
            authorName = await job_service.get_author_name(str(job.author_uid), session)
            return {
                "_id": str(job.uid),
                "title": job.title,
                "description": job.description,
                "type": job.type,
                "likes": job.likes,
                "isLiked": isLiked,  # whether user has liked the job
                "category": job.category,
                "author_uid": str(job.author_uid),
                "authorName": authorName,
                "isActive": job.is_active,
                "status": application.status  # add the application status
            }
