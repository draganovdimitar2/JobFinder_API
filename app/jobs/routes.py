from venv import logger

from fastapi.exceptions import HTTPException
from fastapi.params import Depends
from pygments.lexer import default
from sqlalchemy.testing.suite.test_reflection import users
from sqlalchemy.util import await_only
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth.routes import role_checker
from app.config import Config
from app.auth.schemas import UserCreateModel
from app.db.main import get_session
from app.auth.service import UserService
from app.auth.dependencies import RoleChecker, CustomTokenBearer
from app.jobs.schemas import JobCreateModel, JobResponseModel, JobUpdateModel
from app.jobs.service import JobService
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    status,
)

job_service = JobService()
job_router = APIRouter()
organization_checker = Depends(RoleChecker(['organization']))
access_token_bearer = CustomTokenBearer()  # to requre authentication on each request


@job_router.post('/jobs/add', response_model=JobResponseModel)
async def create_job(
        job_data: JobCreateModel,
        session: AsyncSession = Depends(get_session),
        token_details: dict = Depends(access_token_bearer),
) -> JobResponseModel:
    """
    Endpoint to create a new job listing.
    """
    author_uid = token_details['user']['uid']
    if not author_uid:
        raise HTTPException(status_code=400, detail="Invalid token: author_uid missing")
    return await job_service.create_job(job_data, author_uid, session)


@job_router.patch('/jobs/{job_uid}', response_model=JobResponseModel)
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

    job_to_update = await job_service.get_job(job_uid, session)
    if not job_to_update:
        raise HTTPException(status_code=404, detail="Job not found")
    # check if the author(org) is updating his own jobs, otherwise raise an exception
    if str(job_to_update.author_uid) != user_uid:  # conv to str because first is UUID type and second is str (otherwise our check will always fail)
        raise HTTPException(status_code=403, detail="You are not authorized to update this job!")

    if role != 'organization'.casefold():  # checks if user is trying to update org jobs
        raise HTTPException(status_code=403,
                            detail='Only organizations can update their jobs!')

    updated_job = await job_service.update_job(job_uid, job_update_data, session)
    if not updated_job:  # in case update fails. raise an exception
        raise HTTPException(status_code=500, detail="Job update failed")

    return updated_job


@job_router.get('/jobs/applicants/{author_uid}', response_model=List[JobResponseModel])
async def get_jobs_by_author(
        author_uid: str,
        session: AsyncSession = Depends(get_session),
        token_details: dict = Depends(access_token_bearer)
):
    """
    Endpoint to fetch all jobs by a specific author UID. Including everything (likes, author_uid, active status and so on..).
    """
    user_uid = token_details['user']['uid']

    if user_uid != author_uid:
        raise HTTPException(status_code=403, detail="You are not authorized to view these jobs.")

    return await job_service.get_jobs_by_author_uid(author_uid, session)


@job_router.post('/jobs/{job_uid}/like')
async def like_job(job_uid: str,
                   session: AsyncSession = Depends(get_session),
                   token_details: dict = Depends(access_token_bearer)):
    user_uid = token_details['user']['uid']
    return await job_service.like_job(job_uid, user_uid, session)


@job_router.post('/jobs/{job_uid}/unlike')
async def unlike_job(job_uid: str,
                     session: AsyncSession = Depends(get_session),
                     token_details: dict = Depends(access_token_bearer)):
    user_uid = token_details['user']['uid']
    return await job_service.unlike_job(job_uid, user_uid, session)
