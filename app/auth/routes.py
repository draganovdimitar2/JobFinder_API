from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.main import get_session
from app.auth.service import UserService
from app.auth.dependencies import RoleChecker, CustomTokenBearer
from .security import verify_password, create_access_token
from app.auth.service import upload_to_storage
from fastapi import APIRouter, Depends, UploadFile, File
from app.auth.schemas import (
    UserCreateModel,
    UserLoginModel,
    UserUpdateRequestModel,
    UserPasswordChangeModel
)
from app.errors import (
    InvalidRole,
    UserUsernameAlreadyExists,
    UserEmailAlreadyExists,
    InvalidCredentials,
    UserNotFound,
    InvalidPassword,
    InsufficientPermission
)

access_token_bearer = CustomTokenBearer()
auth_router = APIRouter()
user_service = UserService()
user_role_checker = RoleChecker(['USER'])  # allowed roles
organization_role_checker = RoleChecker(['ORGANIZATION'])


@auth_router.post('/registration')
async def registration(user_data: UserCreateModel,
                       session: AsyncSession = Depends(get_session)):  # Ensure the user is authenticated
    """
    Endpoint for user registration.
    """
    # Check if the role is valid before proceeding with user registration
    allowed_roles = ['ORGANIZATION', 'USER']
    if user_data.role not in allowed_roles:
        raise InvalidRole()

    email = user_data.email  # user's email
    username = user_data.username

    user_email_exists = await user_service.user_exists(email,
                                                       session)  # return a bool based on if user email already exists or not
    username_exists = await user_service.user_exists(username,
                                                     session)  # return a bool based on if username already exists or not

    if user_email_exists:
        raise UserEmailAlreadyExists()
    if username_exists:
        raise UserUsernameAlreadyExists()

    new_user = await user_service.create_user(user_data, session)

    return {"message": "User registered successfully", "user": new_user}


@auth_router.post('/login')
async def login(login_data: UserLoginModel, session: AsyncSession = Depends(get_session)):
    """
    Endpoint for user login.
    """
    credential = login_data.username
    password = login_data.password

    user = await user_service.get_user_by_credential(credential, session)

    if not user:
        raise InvalidCredentials()

    password_valid = verify_password(password, user.password_hash)
    if not password_valid:
        raise InvalidPassword()

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
    """
    Endpoint to fetch user's details.
    """
    user_id = token_details['id']

    user = await user_service.getUserDetails(user_id, session)
    if not user:  # if user cannot be found
        raise UserNotFound()

    return user


@auth_router.get("/user/{user_uid}")
async def get_user(token_details: dict = Depends(access_token_bearer),
                   session: AsyncSession = Depends(get_session)) -> dict:
    """
    Endpoint to fetch user (and his data) by it's uid
    """
    user_id = token_details['id']

    user = await user_service.getUser(user_id, session)
    if not user:  # if user cannot be found
        raise UserNotFound()

    return user


@auth_router.delete('/user/{user_uid}')
async def delete_user(user_uid: str,
                      token_details: dict = Depends(access_token_bearer),
                      session: AsyncSession = Depends(get_session)
                      ) -> dict:
    """
    Endpoint to delete user account.
    """
    current_user_id = token_details['id']
    if str(user_uid) != str(current_user_id):  # checks if current user is trying to delete another user
        raise InsufficientPermission()

    await user_service.deleteUser(user_uid, session)

    return {'message': f"User {token_details['userName']} has been deleted successfully"}


@auth_router.put("/user/{user_uid}")
async def update_user(user_uid: str,
                      user_update: UserUpdateRequestModel,
                      token_details: dict = Depends(access_token_bearer),
                      session: AsyncSession = Depends(get_session)
                      ) -> dict:
    """
    Endpoint to update user info by it's uid.
    """
    current_user_id = token_details['id']
    if str(user_uid) != str(current_user_id):  # checks if current user is trying to update another user
        raise InsufficientPermission()

    user = await user_service.updateUser(user_uid, user_update, session)
    return user


@auth_router.put("/updateUserDetails")
async def update_user(user_update: UserUpdateRequestModel,
                      token_details: dict = Depends(access_token_bearer),
                      session: AsyncSession = Depends(get_session)
                      ) -> dict:  # fetch the user directly from the token
    """
    Endpoint to update user info.
    """
    user_uid = token_details['id']
    user = await user_service.updateUser(user_uid, user_update, session)
    return user


@auth_router.patch("/changePassword")
async def change_user_password(user_data: UserPasswordChangeModel,
                               token_details: dict = Depends(access_token_bearer),
                               session: AsyncSession = Depends(get_session)
                               ) -> dict:
    """
    Endpoint to change user's password.
    """
    user_uid = token_details['id']
    try:
        response = await user_service.changeUserPassword(user_uid, user_data, session)
        return response
    except HTTPException as e:
        raise e


@auth_router.put("/user/{user_uid}/upload_avatar")
async def upload_avatar(token_details: dict = Depends(access_token_bearer), avatar: UploadFile = File(...),
                        session: AsyncSession = Depends(get_session)) -> dict:
    """Endpoint for uploading user avatar (profile picture)"""

    # upload to Azure
    avatar_url = await upload_to_storage(avatar, token_details['id'])

    # update user record in the database with the new avatar URL
    await user_service.updateUser(
        user_id=token_details['id'],
        user_update=UserUpdateRequestModel(avatar_url=avatar_url),
        session=session
    )
    return {"message": "Avatar uploaded and saved successfully", "avatar_url": avatar_url}
