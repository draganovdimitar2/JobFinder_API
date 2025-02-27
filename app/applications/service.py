import uuid

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.applications.schemas import ApplicationRequestModel, ApplicationUpdateModel
from app.jobs.service import JobService
from app.auth.service import UserService
from datetime import datetime
from app.notifications.service import NotificationService
from app.db.models import (
    Jobs,
    User,
    Applications
)
from app.errors import (
    JobNotFound,
    AlreadyApplied,
    ApplicationNotFound,
    InvalidApplicationStatus,
    InsufficientPermission
)


job_service = JobService()
notification_service = NotificationService()
user_service = UserService()


class ApplicationService:

    async def apply_for_job(self,
                            cover_letter: ApplicationRequestModel,
                            user_id: str,
                            job_id: str,
                            session: AsyncSession
                            ) -> dict:
        """Apply for a job"""
        job = await job_service.get_job_by_its_id(job_id, user_id, session)
        if not job:
            raise JobNotFound()

        # check if application is already send for this job
        application_checker = await session.exec(
            select(Applications).where(Applications.user_uid == user_id, Applications.job_uid == job_id))
        application_existence = application_checker.first()

        if application_existence:  # if user has already applied for this offer, raise an exception
            raise AlreadyApplied()

        application = Applications(
            user_uid=user_id,
            job_uid=job_id,
            coverLetter=cover_letter.coverLetter,
            appliedAt=datetime.now()  # Set the appliedAt field
        )
        # trigger the notification
        message = f"You have one new applicant for your job - {job['title']}"
        await notification_service.trigger_notification(uuid.UUID(job['author_uid']), uuid.UUID(user_id), message,
                                                        session, job_id=uuid.UUID(job_id))
        # Add the application to the session
        session.add(application)

        await session.commit()

        application_dict = {
            "_id": str(application.uid),  # Use the instance's uid
            "user": user_id,
            "job": job_id,
            "status": application.status,
            "coverLetter": application.coverLetter,
            "appliedAt": application.appliedAt
        }

        return {"message": "Application submitted successfully",
                "application": application_dict}

    async def my_applications(self,
                              user_id: str,
                              session: AsyncSession
                              ) -> list:
        """Fetch all user applications"""
        statement = await session.exec(select(Applications).where(Applications.user_uid == user_id))
        all_applications = statement.all()
        applications_list = []

        for application in all_applications:
            job_data_dict = await job_service.get_job_by_its_id(application.job_uid, user_id,
                                                                session)  # fetch the job data
            application_dict = {
                "_id": str(application.uid),
                "job": job_data_dict,
                "status": application.status,
                "coverLetter": application.coverLetter,
                "appliedAt": application.appliedAt
            }
            applications_list.append(application_dict)

        return applications_list

    async def get_job_applicants(self, job_id: str, user_id: str, session: AsyncSession) -> list:
        """Get applicants for a job in the desired format"""

        # Fetch Applications and associated Users
        statement = (
            select(Applications, User)
            .join(User, Applications.user_uid == User.uid)  # Join Users to fetch user details
            .where(Applications.job_uid == job_id)  # Filter by job_id
        )

        result = await session.exec(statement)
        records = result.all()

        # Format Application Data
        application_list = [
            {
                "_id": str(application.uid),  # Application ID
                "user": {
                    "_id": str(user.uid),  # User ID
                    "username": user.username,  # Username
                    "email": user.email,  # Email
                    "firstName": user.firstName or "",  # First Name
                    "lastName": user.lastName or "",  # Last Name
                },
                "job": str(application.job_uid),  # Job ID
                "status": application.status,  # Application Status
                "coverLetter": application.coverLetter,  # Cover Letter
                "appliedAt": application.appliedAt.isoformat(),  # Application Date (ISO format)
            }
            for application, user in records
        ]

        return application_list

    async def update_application_status(self,
                                        update_model: ApplicationUpdateModel,
                                        user_id: str,
                                        applications_id: str,
                                        session: AsyncSession) -> dict:
        allowed_application_status = ["PENDING", "ACCEPTED", "REJECTED"]
        if update_model.status not in allowed_application_status:
            raise InvalidApplicationStatus()

        statement = await session.exec(select(Applications).where(Applications.uid == applications_id))
        application = statement.first()  # fetch the application by its id
        if not application:
            raise ApplicationNotFound()

        job_id = application.job_uid  # find the job id from the application
        statement = await session.exec(select(Jobs).where(Jobs.uid == job_id))  # fetch the job from db
        job = statement.first()

        #  Check if application exists and if the user is authorized to update it
        if str(job.author_uid) != user_id:
            raise InsufficientPermission()

        application.status = update_model.status
        # trigger the webhook and add the notification to db
        """Logic will fail if the organization change the job title before the notification has been seen by the user."""
        message = f"Your application status to {job.title} was updated to {application.status}"
        await notification_service.trigger_notification(
            application.user_uid,
            uuid.UUID(user_id),  # conv from str to uuid, because of our db model, otherwise we will get TypeError
            message,
            session,
            application_id=application.uid)
        await session.commit()

        application_dict = {
            "id": str(application.uid),
            "status": application.status,
            "job": str(job.uid)
        }
        return {"message": "Application status updated",
                "application": application_dict}
