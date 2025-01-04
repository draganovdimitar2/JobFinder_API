from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, delete
from app.db.models import Jobs, JobLikes, User, Applications
from app.applications.schemas import ApplicationRequestModel
from app.jobs.service import JobService
from datetime import datetime

job_service = JobService()


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
            raise HTTPException(status_code=400, detail="Job is not active or does not exist")

        # check if application is already send for this job
        application_checker = await session.exec(
            select(Applications).where(Applications.user_uid == user_id, Applications.job_uid == job_id))
        application_existence = application_checker.first()

        if application_existence:  # if like is already given, raise an exception
            raise HTTPException(status_code=400, detail="You have already applied for this job")

        application = Applications(
            user_uid=user_id,
            job_uid=job_id,
            coverLetter=cover_letter.coverLetter,
            appliedAt=datetime.now()  # Set the appliedAt field
        )
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
