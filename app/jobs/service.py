from fastapi.exceptions import HTTPException
from sqlalchemy.testing.suite.test_reflection import users
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from .schemas import JobCreateModel, JobResponseModel, JobUpdateModel
from sqlmodel import select, desc, delete
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

    async def get_jobs_by_author_uid(self, author_uid: str, session: AsyncSession):
        """Fetch jobs associated with a specific author_uid."""
        statement = select(Jobs).where(Jobs.author_uid == author_uid, Jobs.is_active == True)
        result = await session.exec(statement)
        return result.all()

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

    async def update_job(self, job_uid: str, update_data: JobUpdateModel, session: AsyncSession):

        job_to_update = await self.get_job(job_uid, session)

        if job_to_update is not None:
            update_data_dict = update_data.model_dump()

            for k, v in update_data_dict.items():
                setattr(job_to_update, k, v)

            await session.commit()

            return job_to_update
        else:
            return None

    async def like_job(self, job_uid: str, user_uid: str, session: AsyncSession):
        """Allow a user to like a job."""
        # Check if the like of the current user already exists
        job_to_like = await self.get_job(job_uid, session)
        if not job_to_like:
            raise HTTPException(status_code=404, detail="Job not found!")
        if str(job_to_like.author_uid) == user_uid:  # check if the user is owner of the job
            raise HTTPException(status_code=400, detail="You can't like your own job!")

        existing_like = await session.exec(  # checks if the like is already given
            select(JobLikes).where(JobLikes.job_id == job_uid, JobLikes.user_id == user_uid)
        )

        if existing_like.first() is not None:
            raise HTTPException(status_code=400, detail="You have already liked this job")

        # Add the like
        new_like = JobLikes(user_id=user_uid, job_id=job_uid)
        session.add(new_like)

        # Increment the likes count in the Jobs table
        job = await session.exec(select(Jobs).where(Jobs.uid == job_uid))
        job_instance = job.first()

        if job_instance:
            job_instance.likes += 1

        await session.commit()

        return {"message": "Job liked successfully"}

    async def unlike_job(self, job_uid: str, user_uid: str, session: AsyncSession):
        """Allow a user to unlike a job."""
        job_to_unlike = await self.get_job(job_uid, session)
        if not job_to_unlike:
            raise HTTPException(status_code=404, detail="Job not found!")

        if str(job_to_unlike.author_uid) == user_uid:  # check if the user is the owner of the job
            raise HTTPException(status_code=400, detail="You can't unlike your own job!")
        # Check if the like exists
        existing_like_query = select(JobLikes).where(JobLikes.job_id == job_uid, JobLikes.user_id == user_uid)
        existing_like = await session.exec(existing_like_query)

        like_to_remove = existing_like.first()  # fetch the first result
        if not like_to_remove:
            raise HTTPException(status_code=404, detail="You have not liked this job.")

        # Proceed to delete the like
        await session.execute(delete(JobLikes).where(JobLikes.job_id == job_uid, JobLikes.user_id == user_uid))
        # Decrement the likes count in the Jobs table
        job_instance = await session.get(Jobs, job_uid)
        if job_instance:
            job_instance.likes -= 1  # Decrement the likes count

        await session.commit()

        return {"detail": "Job unliked successfully."}
