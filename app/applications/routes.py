from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.main import get_session
from app.applications.service import ApplicationService
from app.applications.schemas import ApplicationRequestModel
from app.auth.dependencies import RoleChecker, CustomTokenBearer
from fastapi import (
    APIRouter,
    Depends,
    status,
)

access_token_bearer = CustomTokenBearer()
application_service = ApplicationService()
application_router = APIRouter()


@application_router.post("/apply/{job_uid}")
async def apply_for_job(job_uid: str,
                        application_data: ApplicationRequestModel,
                        token_details: dict = Depends(access_token_bearer),
                        session: AsyncSession = Depends(get_session)
                        ) -> dict:
    user_id = token_details['id']
    user_role = token_details['roles'][0]
    if user_role != "USER":
        raise HTTPException(status_code=403, detail="Organizations/admins cannot apply for jobs")

    application = await application_service.apply_for_job(application_data, user_id, job_uid, session)
    return application


@application_router.get("/my-applications")
async def my_applications(token_details: dict = Depends(access_token_bearer),
                          session: AsyncSession = Depends(get_session)
                          ) -> list:
    user_id = token_details['id']
    applications = await application_service.my_applications(user_id, session)
    return applications


@application_router.get("/applicants/{job_uid}")
async def get_job_applicants(job_uid: str,
                             token_details: dict = Depends(access_token_bearer),
                             session: AsyncSession = Depends(get_session)) -> list:
    user_id = token_details['id']
    user_role = token_details['roles'][0]
    if user_role != "ORGANIZATION":
        raise HTTPException(status_code=404, detail="Users are not authorized to view job applicants!")

    application = await application_service.get_job_applicants(job_uid, user_id, session)
    return application
