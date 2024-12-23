from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.models import User
from sqlmodel import select
from app.auth.schemas import UserCreateModel
from app.auth.security import generate_password_hash


class UserService:
    async def get_user_by_email(self, email: str,
                                session: AsyncSession):  # func used for login and to check if user exists
        statement = select(User).where(User.email == email)

        result = await session.exec(statement)

        user = result.first()  # get the first user with this e-mail

        return user

    async def get_user_by_credential(self, credential: str,
                                        session: AsyncSession):
        statement = select(User).where((User.username == credential) | (User.email == credential))

        result = await session.exec(statement)

        user = result.first()

        return user

    async def get_user_by_uid(self, user_uid: str,
                              session: AsyncSession):  # func used to get the current user from the token
        statement = select(User).where(User.uid == user_uid)

        result = await session.exec(statement)

        user = result.first()  # get the first user with this UID

        return user

    async def user_exists(self, credential: str, session: AsyncSession):
        user = await self.get_user_by_credential(credential, session)

        return True if user is not None else False

    async def create_user(self, user_data: UserCreateModel, session: AsyncSession):
        user_data_dict = user_data.model_dump()

        new_user = User(
            **user_data_dict
        )

        new_user.password_hash = generate_password_hash(user_data_dict['password'])  # to hash the user password

        session.add(new_user)

        await session.commit()

        return new_user  # This should include first_name and last_name

    async def update_user(self, user: User, user_data: dict, session: AsyncSession):
        for k, v in user_data.items():
            setattr(user, k, v)

        await session.commit()

        return user
