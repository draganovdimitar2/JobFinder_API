from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from app.auth.schemas import UserCreateModel, UserLoginModel
from app.db.main import get_session
from app.auth.service import UserService
from app.auth.dependencies import RoleChecker
from .security import verify_password, create_access_token

from fastapi import (
    APIRouter,
    Depends,
    status,
)

auth_router = APIRouter()
user_service = UserService()
role_checker = RoleChecker(['organization', 'user'])  # allowed roles


@auth_router.post('/auth/registration')
async def registration(user_data: UserCreateModel,
                       session: AsyncSession = Depends(get_session)):  # Ensure the user is authenticated

    # Check if the role is valid before proceeding with user registration
    allowed_roles = ['organization', 'user']  # Define allowed roles here
    if user_data.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{user_data.role}' is not allowed. Allowed roles are: {', '.join(allowed_roles)}."
        )

    email = user_data.email  # user's email

    user_exists = await user_service.user_exists(email, session)  # return a bool based on if user exists or not

    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='User already exists'
        )

    new_user = await user_service.create_user(user_data, session)

    return {"message": "User registered successfully", "user": new_user}


@auth_router.post('/auth/login')
async def login(login_data: UserLoginModel, session: AsyncSession = Depends(get_session)):
    email = login_data.email
    password = login_data.password

    user = await user_service.get_user_by_email(email, session)  # to check if user exists (checks usernames from db)

    if user:  # if user exists
        password_valid = verify_password(password,
                                         user.password_hash)  # check if the password matches the password in our database

        if password_valid:
            access_token = create_access_token(
                user_data={
                    'uid': str(user.uid),  # using str to serialize the UUID
                    'username': user.username,
                    'role': user.role
                }
            )

            return JSONResponse(
                content={
                    "message": "Login successful!",
                    "access_token": access_token,
                    "user": {
                        "email": user.email,
                        "uid": str(user.uid),  # using str to serialize the UUID
                        'role': user.role
                    }
                }
            )

    raise status.HTTP_401_UNAUTHORIZED(detail="Invalid credentials")
