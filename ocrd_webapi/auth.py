from os import getenv
from secrets import compare_digest

from fastapi import HTTPException, status
from fastapi.security import HTTPBasicCredentials


def dummy_security_check(auth: HTTPBasicCredentials):
    """
    Reference security check implementation
    """
    user = auth.username.encode("utf8")
    pw = auth.password.encode("utf8")
    expected_user = getenv("OCRD_WEBAPI_USERNAME", "test").encode("utf8")
    expected_pw = getenv("OCRD_WEBAPI_PASSWORD", "test").encode("utf8")

    user_matched = compare_digest(user, expected_user)
    pw_matched = compare_digest(pw, expected_pw)

    if not user or not pw or not user_matched or not pw_matched:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"}
        )
