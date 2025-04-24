from fastapi import FastAPI, status
from typing import Any, Callable
from fastapi.requests import Request
from fastapi.responses import JSONResponse


class JobFinderException(Exception):
    """This is the base class for all JobFinder errors"""
    pass


class InvalidToken(JobFinderException):
    """User has provided an invalid or expired token"""
    pass


class TokenNotFound(JobFinderException):
    """Token is not found!"""
    pass


class TokenUserRoleMissing(JobFinderException):
    """User role from the token is not found!"""
    pass


class InvalidRole(JobFinderException):
    """Role is not allowed. Allowed roles are USER, ORGANIZATION"""
    pass


class UserEmailAlreadyExists(JobFinderException):
    """User has provided an email for a user who exists during sign up."""
    pass


class UserUsernameAlreadyExists(JobFinderException):
    """User has provided an username for a user who exists during sign up."""
    pass


class LikeOwnJob(JobFinderException):
    """You can't like your own job!"""
    pass


class DislikeOwnJob(JobFinderException):
    """You can't dislike your own job!"""
    pass


class AlreadyLiked(JobFinderException):
    """You have already liked this job"""
    pass


class NotificationNotFound(JobFinderException):
    """Notification is not Found!"""
    pass


class NotificationInsufficientPermission(JobFinderException):
    """You not have the necessary permissions to view this notification!"""
    pass


class LikeNotGiven(JobFinderException):
    """You haven't liked this job"""
    pass


class InvalidCredentials(JobFinderException):
    """User has provided wrong email/username or password during log in."""
    pass


class InvalidPassword(JobFinderException):
    """User has provided an invalid password"""
    pass


class InsufficientPermission(JobFinderException):
    """User does not have the necessary permissions to perform this action."""
    pass


class JobNotFound(JobFinderException):
    """Job Not found"""
    pass


class ApplicationNotFound(JobFinderException):
    """Application Not found"""
    pass


class AlreadyApplied(JobFinderException):
    """You have already applied for this job"""
    pass


class UserNotFound(JobFinderException):
    """User Not found"""
    pass


class AuthorNotFound(JobFinderException):
    """Author Not found"""
    pass


class InvalidApplicationStatus(JobFinderException):
    """Invalid application status. Status can be PENDING, ACCEPTED or REJECTED"""
    pass


class InvalidPictureFormat(JobFinderException):
    """Picture format should be .jpeg, .jpg or .png"""
    pass


def create_exception_handler(
        status_code: int, initial_detail: Any
) -> Callable[[Request, Exception], JSONResponse]:
    async def exception_handler(request: Request, exc: JobFinderException):
        return JSONResponse(content=initial_detail, status_code=status_code)

    return exception_handler


def register_all_errors(app: FastAPI):
    app.add_exception_handler(
        UserEmailAlreadyExists,
        create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            initial_detail={
                "message": "User with this email already exists",
                "error_code": "user_exists",
            },
        ),
    )
    app.add_exception_handler(
        InvalidPictureFormat,
        create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            initial_detail={
                "message": "Picture format should be .jpeg, .jpg or .png",
                "error_code": "invalid_picture_format",
            },
        ),
    )
    app.add_exception_handler(
        TokenNotFound,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail={
                "message": "Token is missing!",
                "error_code": "token_missing",
            },
        ),
    )
    app.add_exception_handler(
        InvalidPassword,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail={
                "message": "Invalid Password!",
                "error_code": "invalid_password",
            },
        ),
    )
    app.add_exception_handler(
        TokenUserRoleMissing,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail={
                "message": "User role from the token is missing!",
                "error_code": "token_role_missing",
            },
        ),
    )
    app.add_exception_handler(
        AuthorNotFound,
        create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND,
            initial_detail={
                "message": "Author not found!",
                "error_code": "author_not_found",
            },
        ),
    )
    app.add_exception_handler(
        NotificationNotFound,
        create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND,
            initial_detail={
                "message": "Notification not found!",
                "error_code": "notification_not_found",
            },
        ),
    )
    app.add_exception_handler(
        NotificationInsufficientPermission,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail={
                "message": "You not have the necessary permissions to view this notification!",
                "error_code": "insufficient_permissions",
            },
        ),
    )
    app.add_exception_handler(
        LikeNotGiven,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "message": "Like is not given!",
                "error_code": "like_not_given",
            },
        ),
    )
    app.add_exception_handler(
        AlreadyLiked,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "message": "You have already liked this job!",
                "error_code": "already_liked",
            },
        ),
    )
    app.add_exception_handler(
        LikeOwnJob,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "message": "You can't like your own job!",
                "error_code": "like_own_job",
            },
        ),
    )
    app.add_exception_handler(
        DislikeOwnJob,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "message": "You can't dislike your own job!",
                "error_code": "dislike_own_job",
            },
        ),
    )
    app.add_exception_handler(
        InvalidApplicationStatus,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "message": "Invalid application status!",
                "error_code": "invalid_application_status",
            },
        ),
    )
    app.add_exception_handler(
        AlreadyApplied,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "message": "You have already applied for this job!",
                "error_code": "already_applied",
            },
        ),
    )
    app.add_exception_handler(
        UserUsernameAlreadyExists,
        create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            initial_detail={
                "message": "User with this username already exists",
                "error_code": "user_exists",
            },
        ),
    )
    app.add_exception_handler(
        InvalidRole,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "message": "Invalid role",
                "error_code": "invalid_role",
            },
        ),
    )
    app.add_exception_handler(
        UserNotFound,
        create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND,
            initial_detail={
                "message": "User not found",
                "error_code": "user_not_found",
            },
        ),
    )
    app.add_exception_handler(
        ApplicationNotFound,
        create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND,
            initial_detail={
                "message": "Application not found",
                "error_code": "application_not_found",
            },
        ),
    )
    app.add_exception_handler(
        InvalidCredentials,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            initial_detail={
                "message": "Invalid Email Or Password",
                "error_code": "invalid_email_or_password",
            },
        ),
    )
    app.add_exception_handler(
        InvalidToken,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail={
                "message": "Token is invalid Or expired",
                "resolution": "Please get new token",
                "error_code": "invalid_token",
            },
        ),
    )
    app.add_exception_handler(
        InsufficientPermission,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            initial_detail={
                "message": "You do not have enough permissions to perform this action",
                "error_code": "insufficient_permissions",
            },
        ),
    )
    app.add_exception_handler(
        JobNotFound,
        create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND,
            initial_detail={
                "message": "Job Not Found",
                "error_code": "job_not_found",
            },
        ),
    )

    @app.exception_handler(500)
    async def internal_server_error(request, exc):
        return JSONResponse(
            content={
                "message": "Oops! Something went wrong",
                "error_code": "server_error",
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
