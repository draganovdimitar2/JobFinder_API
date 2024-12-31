from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from app.auth.schemas import UserCreateModel, UserLoginModel
from app.db.main import get_session
from app.auth.service import UserService
from app.auth.dependencies import RoleChecker, CustomTokenBearer
from .security import verify_password, create_access_token
import logging
import json

logger = logging.getLogger("auth")
from fastapi import (
    APIRouter,
    Depends,
    status,
)

access_token_bearer = CustomTokenBearer()
auth_router = APIRouter()
user_service = UserService()
role_checker = RoleChecker(['ORGANIZATION', 'USER'])  # allowed roles


@auth_router.post('/registration')
async def registration(user_data: UserCreateModel,
                       session: AsyncSession = Depends(get_session)):  # Ensure the user is authenticated

    # Check if the role is valid before proceeding with user registration
    allowed_roles = ['ORGANIZATION', 'USER']  # Define allowed roles here
    if user_data.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{user_data.role}' is not allowed. Allowed roles are: {', '.join(allowed_roles)}."
        )

    email = user_data.email  # user's email
    username = user_data.username

    user_email_exists = await user_service.user_exists(email,
                                                       session)  # return a bool based on if user email already exists or not
    username_exists = await user_service.user_exists(username,
                                                     session)  # return a bool based on if username already exists or not

    if user_email_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Email is already in use'
        )
    if username_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Username already exists'
        )

    new_user = await user_service.create_user(user_data, session)

    return {"message": "User registered successfully", "user": new_user}


@auth_router.post('/login')
async def login(login_data: UserLoginModel, session: AsyncSession = Depends(get_session)):
    credential = login_data.username
    password = login_data.password

    user = await user_service.get_user_by_credential(credential, session)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    password_valid = verify_password(password, user.password_hash)
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token = create_access_token({
        'uid': str(user.uid),
        'username': user.username,
        'role': [user.role]
    })

    return JSONResponse(content={"token": access_token})


@auth_router.get("/userDetails")
async def get_user_details(token_details: dict = Depends(access_token_bearer),
                           session: AsyncSession = Depends(get_session)
                           ) -> dict:
    user_id = token_details['id']

    user = await user_service.getUserDetails(user_id, session)
    if not user:  # if user cannot be found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to retrieve user info"
        )
    return user


@auth_router.get("/user/{user_uid}")
async def get_user(token_details: dict = Depends(access_token_bearer),
                   session: AsyncSession = Depends(get_session)) -> dict:
    user_id = token_details['id']

    user = await user_service.getUser(user_id, session)
    if not user:  # if user cannot be found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to retrieve user info"
        )
    return user


@auth_router.delete('/user/{user_uid}')
async def delete_user(user_uid: str,
                      token_details: dict = Depends(access_token_bearer),
                      session: AsyncSession = Depends(get_session)
                      ):
    current_user_id = token_details['id']
    print(current_user_id)
    if str(user_uid) != str(current_user_id):  # checks if current user is trying to delete another user
        raise HTTPException(status_code=403, detail="You are not authorized to perform this action")

    await user_service.deleteUser(user_uid, session)

    return {'message': f"User {token_details['userName']} has been deleted successfully"}
