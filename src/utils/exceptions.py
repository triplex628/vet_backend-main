from fastapi import status
from fastapi.exceptions import HTTPException

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def not_found_exception(detail: str = 'Not Found') -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"}
    )


def not_authorized_exception(detail: str = 'Incorrect email or password') -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def bad_request_exception(detail: str = 'Bad request') -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )
