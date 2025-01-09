from datetime import timedelta, datetime
from passlib.context import CryptContext
from app.config import Config
import jwt
import logging

passwd_context = CryptContext(
    schemes=['argon2']  # list of the algorithm used to hash the password
)

ACCESS_TOKEN_EXPIRY = 3600


def generate_password_hash(
        password: str) -> str:  # to generate unreadable string of the password which will be stored in our database
    hash = passwd_context.hash(password)

    return hash


def verify_password(password: str, hash: str) -> bool:  # used for log in to verify the password
    return passwd_context.verify(password, hash)


def create_access_token(user: dict, expiry: timedelta = None) -> str:
    payload = {
        'id': user.get('uid'),
        'roles': user.get('role', []),
        'userName': user.get('username'),
        'iat': int(datetime.now().timestamp()),
        'exp': int((datetime.now() + (expiry if expiry is not None else timedelta(minutes=60))).timestamp())
    }

    token = jwt.encode(
        payload=payload,
        key=Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM
    )

    return token


def decode_token(token: str) -> dict:  # to decode the token and check whether it is valid
    try:  # try to decode the token and return it's data
        token_data = jwt.decode(
            jwt=token,
            key=Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGORITHM]  # algorithm to decode the token
        )

        return token_data

    except jwt.PyJWTError as e:  # in case we failed to decode the token
        logging.exception(e)  # to log the error
        return None  # return None if the token is not decoded
