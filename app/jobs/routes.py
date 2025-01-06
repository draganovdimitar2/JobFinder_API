from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.main import get_session
from app.jobs.service import JobService
from app.db.models import User
from typing import List
from app.auth.dependencies import (
    RoleChecker,
    get_current_user,
    CustomTokenBearer
)
from app.jobs.schemas import (
    JobCreateModel,
    JobUpdateModel,
    JobResponseModelWithAuthorName
)
from fastapi import (
    APIRouter,
    Depends
)

job_service = JobService()
job_router = APIRouter()
organization_checker = Depends(RoleChecker(['ORGANIZATION']))
access_token_bearer = CustomTokenBearer()  # to requre authentication on each request


@job_router.post('/add')
async def create_job(
        job_data: JobCreateModel,
        session: AsyncSession = Depends(get_session),
        token_details: dict = Depends(access_token_bearer),
) -> dict:
    """
    Endpoint to create a new job listing.
    """
    author_uid = token_details['id']
    role = token_details['roles'][0]
    if not author_uid:
        raise HTTPException(status_code=400, detail="Invalid token: author_uid missing")
    if role.lower() != 'organization':
        raise HTTPException(status_code=400, detail="Only organizations can create job offers!")
    return await job_service.create_job(job_data, author_uid, session)


@job_router.get('/job')
async def get_all_jobs(
        session: AsyncSession = Depends(get_session),
        token_details: dict = Depends(access_token_bearer)
) -> list:
    """
    Endpoint to fetch all ACTIVE jobs.
    """
    user_id = token_details['id']
    try:
        return await job_service.get_all_jobs(user_id, session)
    except Exception:
        raise HTTPException(status_code=500, detail="An error occurred while trying to fetch all jobs")


@job_router.get('/job/organization')
async def get_organization_jobs(
        session: AsyncSession = Depends(get_session),
        token_details: dict = Depends(access_token_bearer)
) -> list:
    """
    Endpoint to fetch all jobs by a specific author UID. Including everything (likes, author_uid, active status and so on..).
    """
    user_uid = token_details['id']
    role = token_details['roles'][0]

    if role != 'ORGANIZATION':
        raise HTTPException(status_code=403, detail="You are not authorized to view these jobs.")

    return await job_service.get_authors_jobs(user_uid, session)


@job_router.get('/job/{job_uid}')
async def get_job_by_its_id(job_uid: str,
                            session: AsyncSession = Depends(get_session),
                            token_details: dict = Depends(access_token_bearer)) -> dict:
    """
    Fetch a specific job by its UID including author's username and isLiked.
    """
    user_uid = token_details['id']
    job_data = await job_service.get_job_by_its_id(job_uid, user_uid, session)
    return job_data


@job_router.delete("/job/{job_uid}")
async def delete_job(
        job_uid: str,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    """
    Endpoint to delete a job by it's uid.
    """
    return await job_service.delete_job(
        job_uid=job_uid,
        current_user_uid=current_user.uid,
        session=session
    )


@job_router.patch('/job/{job_uid}/deactivate')
async def deactivate_job(job_uid: str,
                         session: AsyncSession = Depends(get_session),
                         token_details: dict = Depends(access_token_bearer)):
    """
    Endpoint to deactivate a job by it's uid.
    """
    user_uid = token_details['id']
    role = token_details['roles'][0]
    username = token_details['userName']
    if role.lower() != 'organization':  # if user is trying to deactivate a job
        raise HTTPException(status_code=403, detail="You are not authorized to deactivate jobs.")

    job = await job_service.get_job_by_its_id(job_uid, user_uid, session)
    if job['author_uid'] != user_uid:  # if job is posted from another user (org)
        raise HTTPException(status_code=403, detail="You are not authorized to deactivate this job!")

    return await job_service.deactivate_job(job_uid, session)


@job_router.patch('/job/{job_uid}/activate')
async def activate_job(job_uid: str,
                       session: AsyncSession = Depends(get_session),
                       token_details: dict = Depends(access_token_bearer)):
    """
    Endpoint to activate a job by it's uid.
    """
    role = token_details['roles'][0]
    user_uid = token_details['id']
    if role.lower() != 'organization':  # if user is trying to activate a job
        raise HTTPException(status_code=403, detail="You are not authorized to activate jobs.")

    job = await job_service.get_inactive_job_data(job_uid, session)
    if str(job.author_uid) != user_uid:  # if job is posted from another user (org). Conv author_uid to str because it is from type UUID.
        raise HTTPException(status_code=403, detail="You are not authorized to deactivate this job!")

    return await job_service.activate_job(job_uid, session)


@job_router.put('/job/{job_uid}')
async def update_job(job_uid: str,
                     job_update_data: JobUpdateModel,
                     session: AsyncSession = Depends(get_session),
                     token_details: dict = Depends(access_token_bearer)
                     ) -> dict:
    """
    Endpoint to update a job. Only organizations can update their own jobs.
    """
    role = token_details['roles'][0]
    user_uid = token_details['id']
    username = token_details['userName']

    job_to_update = await job_service.get_job_by_its_id(job_uid, user_uid, session)
    if not job_to_update:
        raise HTTPException(status_code=404, detail="Job not found")

    # check if the author(org) is updating his own jobs, otherwise raise an exception
    if job_to_update['author_uid'] != user_uid:
        raise HTTPException(status_code=403, detail="You are not authorized to update this job!")

    if role.lower() != 'organization':  # checks if user is trying to update org jobs
        raise HTTPException(status_code=403,
                            detail='Only organizations can update their jobs!')

    await job_service.update_job(job_uid, job_update_data, session)
    job = await job_service.get_job_data(job_uid, session)
    liked_job_user_ids = [str(like.user_id) for like in job.liked_by]

    return {
        "message": "Job updated successfully",
        "job": {
            "_id": job_uid,
            "title": job.title,
            "description": job.description,
            "type": job.type,
            "likes": job.likes,
            "category": job.category,
            "author": user_uid,
            "isActive": job.is_active,
            "authorName": username,
            "applicants": job.applicants,
            "likedBy": liked_job_user_ids
        }
    }


@job_router.post('/job/{job_uid}/like')
async def like_job(job_uid: str,
                   session: AsyncSession = Depends(get_session),
                   token_details: dict = Depends(access_token_bearer)):
    """
    Endpoint to like a specific job.
    """
    user_uid = token_details['id']

    job_data = await job_service.get_job_data(job_uid, session)
    job_author_uid = job_data.author_uid

    if str(job_author_uid) == user_uid:  # check if the user is owner of the job
        raise HTTPException(status_code=400, detail="You can't like your own job!")

    if await job_service.like_checker(user_uid, job_uid, session):  # check whether like is already given
        raise HTTPException(status_code=400, detail="You have already liked this job")

    return await job_service.like_job(job_uid, user_uid, session)


@job_router.delete('/job/{job_uid}/like')
async def unlike_job(job_uid: str,
                     session: AsyncSession = Depends(get_session),
                     token_details: dict = Depends(access_token_bearer)):
    """
    Endpoint to unlike a specific job.
    """
    user_uid = token_details['id']

    job_data = await job_service.get_job_data(job_uid, session)
    job_author_uid = job_data.author_uid

    if str(job_author_uid) == user_uid:  # check if the user is owner of the job
        raise HTTPException(status_code=400, detail="You can't unlike your own job!")

    if not await job_service.like_checker(user_uid, job_uid, session):  # check whether like is already given
        raise HTTPException(status_code=400, detail="Trying to dislike a job that you haven't like yet!")

    return await job_service.unlike_job(job_uid, user_uid, session)


@job_router.get('/favorites')
async def get_all_liked_jobs(
        session: AsyncSession = Depends(get_session),
        token_details: dict = Depends(access_token_bearer)
) -> list:
    user_uid = token_details['id']
    try:
        return await job_service.get_liked_jobs(user_uid, session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
