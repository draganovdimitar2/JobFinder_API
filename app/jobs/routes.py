from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.main import get_session
from app.jobs.service import JobService
from typing import List
from app.auth.dependencies import (
    RoleChecker,
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
organization_checker = Depends(RoleChecker(['organization']))
access_token_bearer = CustomTokenBearer()  # to requre authentication on each request


@job_router.post('/jobs/add')
async def create_job(
        job_data: JobCreateModel,
        session: AsyncSession = Depends(get_session),
        token_details: dict = Depends(access_token_bearer),
) -> dict:
    """
    Endpoint to create a new job listing.
    """
    author_uid = token_details['user']['uid']
    role = token_details['user']['role']
    if not author_uid:
        raise HTTPException(status_code=400, detail="Invalid token: author_uid missing")
    if role.lower() != 'organization':
        raise HTTPException(status_code=400, detail="Only organizations can create job offers!")
    return await job_service.create_job(job_data, author_uid, session)


@job_router.patch('/jobs/{job_uid}', response_model=JobResponseModelWithAuthorName)
async def update_job(job_uid: str,
                     job_update_data: JobUpdateModel,
                     session: AsyncSession = Depends(get_session),
                     token_details: dict = Depends(access_token_bearer)
                     ) -> dict:
    """
    Endpoint to update a job. Only organizations can update their own jobs.
    """
    role = token_details['user']['role']
    user_uid = token_details['user']['uid']
    username = token_details['user']['username']

    job_to_update = await job_service.get_job_by_its_id(job_uid, user_uid, session)
    if not job_to_update:
        raise HTTPException(status_code=404, detail="Job not found")
    # check if the author(org) is updating his own jobs, otherwise raise an exception
    if str(job_to_update[
               'authorName']) != username:  # conv to str because first is UUID type and second is str (otherwise our check will always fail)
        raise HTTPException(status_code=403, detail="You are not authorized to update this job!")

    if role.lower() != 'organization':  # checks if user is trying to update org jobs
        raise HTTPException(status_code=403,
                            detail='Only organizations can update their jobs!')

    await job_service.update_job(job_uid, user_uid, job_update_data, session)
    updated_job = await job_service.get_job_by_its_id(job_uid, user_uid,
                                                      session)  # Using second await to hide some job data in the response

    return updated_job


# @job_router.get('/jobs/{job_uid}', response_model=JobResponseModel)
# async def get_job(job_uid: str,
#                   session: AsyncSession = Depends(get_session),
#                   _: dict = Depends(access_token_bearer)) -> JobResponseModel:
#     try:
#         return await job_service.get_job(job_uid, session)
#     except Exception as e:
#         raise HTTPException(status_code=404, detail=e)


@job_router.get('/jobs/{job_uid}', response_model=JobResponseModelWithAuthorName)
async def get_job_by_its_id(job_uid: str,
                            session: AsyncSession = Depends(get_session),
                            token_details: dict = Depends(access_token_bearer)) -> dict:
    """
    Fetch a specific job by its UID including author's username and isLiked.
    """
    user_uid = token_details['user']['uid']
    job_data = await job_service.get_job_by_its_id(job_uid, user_uid, session)
    return job_data


@job_router.get('/jobs/applicants/{author_uid}', response_model=List[JobResponseModelWithAuthorName])
async def get_authors_jobs(
        session: AsyncSession = Depends(get_session),
        token_details: dict = Depends(access_token_bearer)
):
    """
    Endpoint to fetch all jobs by a specific author UID. Including everything (likes, author_uid, active status and so on..).
    """
    user_uid = token_details['user']['uid']
    role = token_details['user']['role']

    if role != 'organization':
        raise HTTPException(status_code=403, detail="You are not authorized to view these jobs.")

    return await job_service.get_authors_jobs(user_uid, session)


@job_router.post('/jobs/{job_uid}/like')
async def like_job(job_uid: str,
                   session: AsyncSession = Depends(get_session),
                   token_details: dict = Depends(access_token_bearer)):
    """
    Endpoint to like a specific job.
    """
    user_uid = token_details['user']['uid']
    return await job_service.like_job(job_uid, user_uid, session)


@job_router.post('/jobs/{job_uid}/unlike')
async def unlike_job(job_uid: str,
                     session: AsyncSession = Depends(get_session),
                     token_details: dict = Depends(access_token_bearer)):
    """
    Endpoint to unlike a specific job.
    """
    user_uid = token_details['user']['uid']
    return await job_service.unlike_job(job_uid, user_uid, session)
