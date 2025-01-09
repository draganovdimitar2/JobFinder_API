from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.main import get_session
from app.jobs.service import JobService
from app.db.models import User
from app.auth.dependencies import (
    RoleChecker,
    get_current_user,
    CustomTokenBearer
)
from app.errors import (
    JobNotFound,
    InsufficientPermission,
    LikeOwnJob,
    DislikeOwnJob,
    AlreadyLiked,
    LikeNotGiven
)
from app.jobs.schemas import (
    JobCreateModel,
    JobUpdateModel
)
from fastapi import (
    APIRouter,
    Depends
)

job_service = JobService()
job_router = APIRouter()
user_role_checker = RoleChecker(['USER'])  # user role for RBAC
organization_role_checker = RoleChecker(['ORGANIZATION'])  # org role for RBAC
access_token_bearer = CustomTokenBearer()  # to requre authentication on each request


@job_router.post('/add')
async def create_job(
        job_data: JobCreateModel,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(organization_role_checker),  # implement RBAC
) -> dict:
    """
    Endpoint to create a new job listing.
    """
    return await job_service.create_job(job_data, str(current_user.uid), session)


@job_router.get('/job')
async def get_all_jobs(
        session: AsyncSession = Depends(get_session),
        token_details: dict = Depends(access_token_bearer)
) -> list:
    """
    Endpoint to fetch all ACTIVE jobs.
    """
    user_id = token_details['id']
    return await job_service.get_all_jobs(user_id, session)


@job_router.get('/job/organization')
async def get_organization_jobs(
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(organization_role_checker)
) -> list:
    """
    Endpoint to fetch all jobs created by organization
    """
    return await job_service.get_authors_jobs(str(current_user.uid), session)


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
                         current_user: User = Depends(organization_role_checker)):
    """
    Endpoint to deactivate a job by it's uid.
    """
    job = await job_service.get_job_by_its_id(job_uid, str(current_user.uid), session)
    if job['author_uid'] != str(current_user.uid):  # if job is posted from another user (org)
        raise InsufficientPermission()

    return await job_service.deactivate_job(job_uid, session)


@job_router.patch('/job/{job_uid}/activate')
async def activate_job(job_uid: str,
                       session: AsyncSession = Depends(get_session),
                       current_user: User = Depends(organization_role_checker)):
    """
    Endpoint to activate a job by it's uid.
    """
    job = await job_service.get_inactive_job_data(job_uid, session)
    if str(job.author_uid) != str(
            current_user.uid):  # if job is posted from another user (org). Conv author_uid to str because it is from type UUID.
        raise InsufficientPermission()

    return await job_service.activate_job(job_uid, session)


@job_router.put('/job/{job_uid}')
async def update_job(job_uid: str,
                     job_update_data: JobUpdateModel,
                     session: AsyncSession = Depends(get_session),
                     current_user: User = Depends(organization_role_checker)
                     ) -> dict:
    """
    Endpoint to update a job. Only organizations can update their own jobs.
    """
    job_to_update = await job_service.get_job_by_its_id(job_uid, str(current_user.uid), session)
    if not job_to_update:
        raise JobNotFound()

    # check if the author(org) is updating his own jobs, otherwise raise an exception
    if job_to_update['author_uid'] != str(current_user.uid):
        raise InsufficientPermission()

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
            "author": str(current_user.uid),
            "isActive": job.is_active,
            "authorName": current_user.username,
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
    if not job_data:
        raise JobNotFound()

    job_author_uid = job_data.author_uid

    if str(job_author_uid) == user_uid:  # check if the user is owner of the job
        raise LikeOwnJob()

    if await job_service.like_checker(user_uid, job_uid, session):  # check whether like is already given
        raise AlreadyLiked()

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
    if not job_data:
        raise JobNotFound()
    job_author_uid = job_data.author_uid

    if str(job_author_uid) == user_uid:  # check if the user is owner of the job
        raise DislikeOwnJob()

    if not await job_service.like_checker(user_uid, job_uid, session):  # check whether like is already given
        raise LikeNotGiven()

    return await job_service.unlike_job(job_uid, user_uid, session)


@job_router.get('/favorites')
async def get_all_liked_jobs(
        session: AsyncSession = Depends(get_session),
        token_details: dict = Depends(access_token_bearer)
) -> list:
    """
    Endpoint to fetch all liked jobs by current user.
    """
    user_uid = token_details['id']
    return await job_service.get_liked_jobs(user_uid, session)
