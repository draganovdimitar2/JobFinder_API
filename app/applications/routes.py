from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.main import get_session
from app.db.models import User
from app.applications.service import ApplicationService
from app.applications.schemas import ApplicationRequestModel, ApplicationUpdateModel
from app.auth.dependencies import RoleChecker, CustomTokenBearer
from fastapi import APIRouter, Depends

user_role_checker = RoleChecker(['USER'])  # user role for RBAC
organization_role_checker = RoleChecker(['ORGANIZATION'])  # org role for RBAC
access_token_bearer = CustomTokenBearer()
application_service = ApplicationService()
application_router = APIRouter()


@application_router.post("/apply/{job_uid}")
async def apply_for_job(job_uid: str,
                        application_data: ApplicationRequestModel,
                        current_user: User = Depends(user_role_checker),  # implement the RBAC
                        session: AsyncSession = Depends(get_session)
                        ) -> dict:
    """
    Endpoint to apply for a job by it's uid.
    """
    application = await application_service.apply_for_job(application_data, str(current_user.uid), job_uid, session)
    return application


@application_router.get("/my-applications")
async def my_applications(current_user: User = Depends(user_role_checker),
                          session: AsyncSession = Depends(get_session)
                          ) -> list:
    """
    Endpoint to fetch all user's applications.
    """
    applications = await application_service.my_applications(str(current_user.uid), session)
    return applications


@application_router.get("/applicants/{job_uid}")
async def get_job_applicants(job_uid: str,
                             current_user: User = Depends(organization_role_checker),
                             session: AsyncSession = Depends(get_session)) -> list:
    """
    Endpoint to fetch all applicants to specific job.
    """
    application = await application_service.get_job_applicants(job_uid, str(current_user.uid), session)
    return application


@application_router.patch("/application/{application_uid}/status")
async def update_application_status(application_uid: str,
                                    update_data: ApplicationUpdateModel,
                                    current_user: User = Depends(organization_role_checker),
                                    session: AsyncSession = Depends(get_session)) -> dict:
    """
    Endpoint to update application status.
    """
    application_status_update = await application_service.update_application_status(update_data, str(current_user.uid),
                                                                                    application_uid, session)
    return application_status_update
