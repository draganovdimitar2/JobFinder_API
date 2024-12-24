from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from app.db.models import User
from app.db.main import get_session
from .service import UserService
from .security import decode_token

user_service = UserService()


class TokenBearer(HTTPBearer):  # Base Class for Token Validation

    def __init__(self, auto_error=True):  # to determine the behaviour of our class if an error occurs
        super().__init__(
            auto_error=auto_error)  # this is going to call the __init__ method of our parent class (HTTPBearer class)

    async def __call__(self,
                       request: Request) -> dict:  # __call__ method makes the class callable, allowing it to be used as a dependency
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        token = credentials.credentials  # Extract token from Authorization header

        token_data = decode_token(token)

        if not self.token_valid(token):
            raise HTTPException(
                status_code=403,
                detail="Authorization token is invalid."
            )

        self.verify_token_data(token_data)

        return token_data

    def token_valid(self, token: str) -> bool:  # func to check whether our token is valid

        token_data = decode_token(token)

        return token_data is not None  # return True if it's not None else it will return False

    def verify_token_data(self, token_data):
        raise NotImplementedError(
            "Please Override this method in child classes")  # throwing an error if this method is not override


class CustomTokenBearer(TokenBearer):

    def verify_token_data(self, token_data: dict) -> None:

        if not token_data:  # if token is not found
            raise HTTPException(status_code=401, detail="Token missing!")
        if not token_data['roles']:  # if user role can't be found in token
            raise HTTPException(status_code=401, detail="Invalid token: Missing user or role data.")
        if token_data['exp'] - token_data['iat'] <= 0:  # if token time has passed
            raise HTTPException(status_code=401, detail="Token has expired, please login again.")


async def get_current_user(
        token_details: dict = Depends(CustomTokenBearer()),
        session: AsyncSession = Depends(get_session)
):
    if not token_details:
        raise HTTPException(status_code=403, detail="Invalid token: User data missing.")

    user_uid = token_details['id']
    user = await user_service.get_user_by_uid(user_uid, session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    return user


class RoleChecker:

    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles  # These will be the roles that are authorized to perform a certain action

    def __call__(self, current_user: User = Depends(
        get_current_user)):
        if current_user.role.upper() in [role.upper() for role in self.allowed_roles]:
            return True  # indicating the user has permission

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have sufficient permissions to perform this action."
        )
