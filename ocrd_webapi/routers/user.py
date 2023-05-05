"""
module for implementing the authentication section of the api
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from ocrd_webapi.authentication import authenticate_user, register_user

router = APIRouter(
    tags=["User"],
)

logger = logging.getLogger(__name__)
# TODO: This may not be ideal, discussion needed
security = HTTPBasic()


@router.get("/user/login")
async def user_login(auth: HTTPBasicCredentials = Depends(security)):
    email = auth.username
    password = auth.password
    if not (email and password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"},
            detail="Missing e-mail or password field"
        )

    # Authenticate user e-mail and password
    try:
        await authenticate_user(
            email=email,
            password=password
        )
    except ValueError as error:
        logger.info(f"User failed to authenticate: {email}, reason: {error}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"},
            detail=f"{error}"
        )

    return {"200": {"model": "Successfully logged!"}}


@router.post("/user/register")
async def user_register(email: str, password: str):
    try:
        await register_user(
            email=email,
            password=password,
            validated_account=False
        )
    except ValueError as error:
        logger.info(f"User failed to register: {email}, reason: {error}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            headers={"WWW-Authenticate": "Basic"},
            detail=f"{error}"
        )

    return {"201": {"message": f"Successfully registered new account: {email}. "
                               f"Please contact the OCR-D team to get your account validated."}}
