from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.exceptions import HTTPException
from app.db.models import User, JobLikes, Applications, Jobs
from sqlmodel import select, delete, update, values
from app.auth.schemas import UserCreateModel, UserUpdateRequestModel, UserPasswordChangeModel
from app.auth.security import generate_password_hash, verify_password


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

    async def getUserDetails(self, user_id: str, session: AsyncSession):
        user = await self.get_user_by_uid(user_id, session)
        user_response_dict = {
            # not using schemas, because Pydantic automatically excludes fields prefixed with an underscore
            '_id': user.uid,
            'username': user.username,
            'email': user.email,
            'roles': [user.role],
            'firstName': user.firstName,
            'lastName': user.lastName,
            'isActive': user.is_active
        }
        return user_response_dict

    async def getUser(self, user_id: str, session: AsyncSession):
        user = await self.get_user_by_uid(user_id, session)
        user_response_dict = {
            # not using schemas, because Pydantic automatically excludes fields prefixed with an underscore
            '_id': user.uid,
            'username': user.username,
            'email': user.email,
            'password': user.password_hash,
            'roles': [user.role],
            'firstName': user.firstName,
            'lastName': user.lastName,
            'applications': user.applications,
            'isActive': user.is_active
        }
        return user_response_dict

    async def deleteUser(self, user_id: str, session: AsyncSession):
        user = await self.get_user_by_uid(user_id, session)  # fetch the user from the db
        if not user:  # if user cannot be found
            raise HTTPException(status_code=404, detail="User could not be found")

        # Remove likes by the user from all jobs
        statement = select(JobLikes).where(JobLikes.user_id == user_id)
        result = await session.exec(statement)
        job_likes = result.all()  # Fetch all JobLikes instances

        # Iterate through each job_like and delete it
        for job_like in job_likes:
            await session.delete(job_like)

        # Determine user role
        role = user.role

        if role == 'USER':  # remove all applications made by the user
            statement = delete(Applications).where(Applications.user_uid == user_id)
            await session.exec(statement)

        if role == 'ORGANIZATION':  # Set all jobs created by the organization to inactive (without touching the likes)
            statement = update(Jobs).where(Jobs.uid == user_id).values(is_active=False)
            await session.execute(statement)

        # Finally delete the user
        await session.delete(user)
        await session.commit()

    async def updateUser(self, user_id: str, user_update: UserUpdateRequestModel, session: AsyncSession):
        user = await self.get_user_by_uid(user_id, session)  # fetch the user from the db
        if not user:  # if user cannot be found
            raise HTTPException(status_code=404, detail="User could not be found")

        # Validate unique constraints
        username_existence = await self.get_user_by_credential(user_update.username, session)
        if username_existence and username_existence.username != user.username:
            raise HTTPException(status_code=400, detail="Username already in use")

        email_existence = await self.get_user_by_credential(user_update.email, session)
        if email_existence and email_existence.email != user.email:
            raise HTTPException(status_code=400, detail="Email already in use")

        # Update fields only if new values are provided
        if user_update.username:
            user.username = user_update.username

        if user_update.email:
            user.email = user_update.email

        if user_update.firstName:
            user.firstName = user_update.firstName

        if user_update.lastName:
            user.lastName = user_update.lastName

        await session.commit()

        return {"message": f"User {user.username} has been updated successfully",
                "data": {
                    "username": {user.username},
                    "email": {user.email}
                }
                }

    async def changeUserPassword(self, user_uid: str, user_data: UserPasswordChangeModel, session: AsyncSession):
        user = await self.get_user_by_uid(user_uid, session)  # fetch the user from the db
        if not user:  # if user cannot be found
            raise HTTPException(status_code=404, detail="User could not be found")

        user_password_from_db = user.password_hash  # get the hashed password from db

        password_verify = verify_password(user_data.oldPassword, user_password_from_db)  # return a bool based on whether old password from user is the same as this in the db
        if not password_verify:  # if old password is not the same
            raise HTTPException(status_code=400, detail="Invalid old password")

        hashed_new_user_password = generate_password_hash(user_data.newPassword)  # generate hash for the new password
        user.password_hash = hashed_new_user_password

        await session.commit()  # add the changed password to db
        return {"message": "Password changed successfully"}
