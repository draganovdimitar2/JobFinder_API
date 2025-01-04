from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from .schemas import JobCreateModel, JobUpdateModel
from sqlmodel import select, delete
from app.db.models import Jobs, JobLikes, User


class JobService:
    async def get_all_jobs(self, user_uid: str, session: AsyncSession):
        """Fetch all active jobs."""
        statement = select(Jobs).where(Jobs.is_active == True)

        result = await session.exec(statement)

        all_jobs = result.all()

        list_storing_all_jobs = []
        for job in all_jobs:  # for each job we get its authorName and check if current user has liked the job
            authorName = await self.get_author_name(job.author_uid, session)
            isLiked = await self.like_checker(user_uid, str(job.uid), session)
            job_response_dict = {
                "_id": str(job.uid),
                "title": job.title,
                "description": job.description,
                "type": job.type,
                "likes": job.likes,
                "category": job.category,
                "isActive": job.is_active,
                "authorName": authorName,  # Add the author's username
                "isLiked": isLiked
            }
            list_storing_all_jobs.append(job_response_dict)

        return list_storing_all_jobs

    async def get_organization_jobs(self, organization_uid: str, session: AsyncSession):
        """Fetch all active jobs for a specific organization."""
        statement = (
            select(Jobs)
            .where(Jobs.author_uid == organization_uid, Jobs.is_active == True)
        )

        result = await session.exec(statement)

        return result.all()

    async def get_job_data(self, job_uid: str, session: AsyncSession):
        """Fetch a specific ACTIVE job by its UID. RESPONSE INCLUDE ALL DATA ABOUT THE ACTIVE JOB"""
        statement = select(Jobs).where(Jobs.uid == job_uid, Jobs.is_active == True)

        result = await session.exec(statement)

        job = result.first()

        return job if job is not None else None  # if job is not none return the job, else return None

    async def get_inactive_job_data(self, job_uid: str, session: AsyncSession):
        """Fetch a specific INACTIVE job by its UID. RESPONSE INCLUDE ALL DATA ABOUT THE INACTIVE JOB"""
        statement = select(Jobs).where(Jobs.uid == job_uid, Jobs.is_active == False)

        result = await session.exec(statement)

        job = result.first()

        return job if job is not None else None  # if job is not none return the job, else return None

    async def get_job_by_its_id(self, job_uid: str, user_uid: str, session: AsyncSession):
        """Fetch a specific job by its UID including author's username and isLiked."""
        # Query the job
        statement = select(Jobs).where(Jobs.uid == job_uid, Jobs.is_active == True)
        result = await session.exec(statement)
        job = result.first()

        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        job_dict = {
            "_id": str(job_uid),
            "title": job.title,
            "description": job.description,
            "type": job.type,
            "likes": job.likes,
            "category": job.category,
            "isActive": job.is_active,
            "isLiked": False  # default value
        }

        if await self.like_checker(user_uid, job_uid, session):
            job_dict["isLiked"] = True
        author_uid = job.author_uid
        author_username = await self.get_author_name(author_uid, session)
        job_dict['authorName'] = author_username  # Add the author's username to the response

        return job_dict

    async def get_author_name(self, author_uid: str, session: AsyncSession) -> str:
        """Fetch the author's username based on author_uid."""
        statement = select(User.username).where(User.uid == author_uid)
        result = await session.execute(statement)
        author = result.scalars().first()  # Get the first matching author

        if author is None:
            raise HTTPException(status_code=404, detail="Author not found")

        return author  # Return the author's username

    async def get_authors_jobs(self, author_uid: str, session: AsyncSession):
        """Fetch all jobs associated with a specific author_uid."""
        statement = select(Jobs).where(Jobs.author_uid == author_uid)
        result = await session.exec(statement)
        jobs = result.all()

        enriched_jobs = []
        for job in jobs:
            # Enrich the job with author name
            author_username = await self.get_author_name(job.author_uid, session)
            isLiked = await self.like_checker(author_uid, str(job.uid), session)
            liked_job_user_ids = [str(like.user_id) for like in job.liked_by]
            applicants_list = [{"_id": str(applicant.uid)} for applicant in job.applicants]
            job_dict = {
                "_id": str(job.uid),
                "title": job.title,
                "description": job.description,
                "type": job.type,
                "likes": job.likes,
                "category": job.category,
                "author": str(job.author_uid),
                "isActive": job.is_active,
                "authorName": author_username,  # Add the author's username
                "isLiked": isLiked,
                "applicants": applicants_list,
                "likedBy": liked_job_user_ids  # to show only the users id
            }
            enriched_jobs.append(job_dict)

        return enriched_jobs

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
                "_id": job.uid,
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

    async def create_job(self, job_data: JobCreateModel, author_uid: str, session: AsyncSession) -> dict:
        """Create a new job and return the created job instance."""
        new_job = Jobs(**job_data.dict(), author_uid=author_uid)
        session.add(new_job)
        await session.commit()
        await session.refresh(new_job)
        return {"message": "Job offer has been created successfully."}

    async def update_job(self, job_uid: str, update_data: JobUpdateModel, session: AsyncSession):
        job_to_update = await self.get_job_data(job_uid, session)  # taking all job data

        if job_to_update is not None:
            update_data_dict = update_data.model_dump()

            for k, v in update_data_dict.items():
                setattr(job_to_update, k, v)

            await session.commit()

            return job_to_update
        else:
            return None

    async def like_checker(self, user_uid: str, job_uid: str, session: AsyncSession):
        """Function to check whether current user has liked the job"""
        existing_like = await session.exec(  # checks if the user has liked the job
            select(JobLikes).where(JobLikes.job_id == job_uid, JobLikes.user_id == user_uid)
        )
        if existing_like.first() is not None:
            return True  # if job is already liked by the user
        return False  # else: return False

    async def like_job(self, job_uid: str, user_uid: str, session: AsyncSession):
        """Allow a user to like a job."""
        job = await self.get_job_by_its_id(job_uid, user_uid, session)
        if not job:  # if job is not found
            raise HTTPException(status_code=404, detail="Job is not found!")

        # Add the like
        new_like = JobLikes(user_id=user_uid, job_id=job_uid)
        session.add(new_like)

        # Increment the likes count in the Jobs table
        job = await session.exec(select(Jobs).where(Jobs.uid == job_uid))
        job_instance = job.first()

        if job_instance:
            job_instance.likes += 1

        await session.commit()

        return {
            "message": "Job liked",
            "likes": job_instance.likes,
            "isLiked": True
        }

    async def unlike_job(self, job_uid: str, user_uid: str, session: AsyncSession):
        """Allow a user to unlike a job."""
        job = await self.get_job_by_its_id(job_uid, user_uid, session)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found!")

        # Proceed to delete the like
        await session.exec(delete(JobLikes).where(JobLikes.job_id == job_uid, JobLikes.user_id == user_uid))
        # Decrement the likes count in the Jobs table
        job_instance = await session.get(Jobs, job_uid)
        if job_instance:
            job_instance.likes -= 1  # Decrement the likes count

        await session.commit()

        return {
            "message": "Job unliked",
            "likes": job_instance.likes,
            "isLiked": False
        }

    async def get_liked_jobs(self, user_uid: str, session: AsyncSession):
        """Fetch all liked jobs from current user"""
        statement = select(JobLikes).where(JobLikes.user_id == user_uid)  # fetch liked jobs uid

        result = await session.exec(statement)

        all_liked_jobs_by_user = result.all()

        all_liked_jobs_list = []

        for job_id in all_liked_jobs_by_user:  # iterate through liked job id's
            job_uid = job_id.job_id
            job = await self.get_job_by_its_id(job_uid, user_uid, session)  # fetch the job by its id
            all_liked_jobs_list.append(job)

        return all_liked_jobs_list

    async def deactivate_job(self, job_uid: str, session: AsyncSession):
        """Deactivate a job by its uid."""
        job = await self.get_job_data(job_uid, session)
        job.is_active = False
        session.add(job)
        await session.commit()
        return {"message": "Job deactivated successfully"}

    async def activate_job(self, job_uid: str, session: AsyncSession):
        """Activate a job by its uid."""
        job = await self.get_inactive_job_data(job_uid, session)
        job.is_active = True
        session.add(job)
        await session.commit()
        return {"message": "Job activated successfully"}

    async def delete_job(self, job_uid: str, current_user_uid: str, session: AsyncSession):
        """Fetch and delete a job if the current user is the author."""
        # Query the job by its UID
        query = select(Jobs).where(Jobs.uid == job_uid)
        result = await session.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Check if the current user is the author of the job
        if job.author_uid != current_user_uid:
            raise HTTPException(status_code=403, detail="You do not have permission to delete this job")

        job_likes_query = select(JobLikes).where(
            JobLikes.job_id == job_uid
        )
        result = await session.exec(job_likes_query)
        job_likes = result.all()  # Get all related JobLikes

        for job_like in job_likes:  # iterate through each like and delete it
            await session.delete(job_like)

        # Delete the job and commit the transaction
        await session.delete(job)

        await session.commit()

        return {"detail": "Job deleted successfully"}
