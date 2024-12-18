from venv import logger

from fastapi.exceptions import HTTPException
from fastapi.params import Depends
from sqlalchemy.testing.suite.test_reflection import users
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth.routes import role_checker
from app.config import Config
from app.auth.schemas import UserCreateModel
from app.db.main import get_session
from app.auth.service import UserService
from app.auth.dependencies import RoleChecker, CustomTokenBearer
from app.jobs.schemas import JobCreateModel, JobResponseModel
from app.jobs.service import JobService
from app.db.models import Jobs

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
    author_uid = token_details.get("user", {}).get("uid")
    if not author_uid:
        raise HTTPException(status_code=400, detail="Invalid token: author_uid missing")
    return await job_service.create_job(job_data, author_uid, session)
