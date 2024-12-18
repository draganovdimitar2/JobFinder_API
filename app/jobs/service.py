from sqlalchemy.testing.suite.test_reflection import users
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from .schemas import JobCreateModel, JobResponseModel
from sqlmodel import select, desc
from app.db.models import Jobs, JobLikes, Applications, User
from datetime import datetime


class JobService:
    async def get_all_jobs(self, session: AsyncSession):
        """Fetch all active jobs."""
        statement = select(Jobs).where(Jobs.is_active == True)

        result = await session.exec(statement)

        return result.all()

    async def get_organization_jobs(self, organization_uid: str, session: AsyncSession):
        """Fetch all active jobs for a specific organization."""
        statement = (
            select(Jobs)
            .where(Jobs.author_uid == organization_uid, Jobs.is_active == True)
        )

        result = await session.exec(statement)

        return result.all()

    async def get_job(self, job_uid: str, session: AsyncSession):
        """Fetch a specific job by its UID."""
        statement = select(Jobs).where(Jobs.uid == job_uid, Jobs.is_active == True)

        result = await session.exec(statement)

        job = result.first()

        return job if job is not None else None  # if job is not none return the job, else return None

    async def get_job_appliciants(self, job_uid: str, session: AsyncSession):
        """Fetch the applicants for a specific job."""
        statement = (
            select(Jobs)
            .where(Jobs.uid == job_uid)
            .options(selectinload(Jobs.applicants))  # Eager load the applicants
        )

        result = await session.exec(statement)

        job = result.scalar_one_or_none()  # Retrieve the job or None if it doesn't exist

        if job:
            # Extract the UIDs of the applicants
            applicant_uids = [application.user_uid for application in job.applicants]

            return {
                "uid": job.uid,
                "title": job.title,
                "description": job.description,
                "type": job.type,
                "likes": job.likes,
                "category": job.category,
                "author_uid": job.author_uid,
                "isActive": job.is_active,
                "applicants": applicant_uids,  # Return only UIDs of applicants
            }

        return None  # Return None if no job found

    async def create_job(self, job_data: JobCreateModel, author_uid: str, session: AsyncSession) -> Jobs:
        """Create a new job and return the created job instance."""
        new_job = Jobs(**job_data.dict(), author_uid=author_uid)
        session.add(new_job)
        await session.commit()
        await session.refresh(new_job)
        return new_job
