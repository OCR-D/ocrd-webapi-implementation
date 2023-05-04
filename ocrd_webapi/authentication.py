from hashlib import sha512
from random import random
from typing import Tuple

from .database import create_user, get_user

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


async def authenticate_user(email: str, password: str):
    db_user = await get_user(email=email)
    if not db_user:
        raise ValueError(f"User not found: {email}")
    validation_status = validate_password(
        plain_password=password,
        encrypted_password=db_user.encrypted_pass
    )
    if not validation_status:
        raise ValueError(f"User was not validated: {email}")


async def register_user(email: str, password: str):
    salt, encrypted_password = encrypt_password(password)
    db_user = await get_user(email)
    if db_user:
        raise ValueError(f"User is already registered: {email}")
    created_user = await create_user(
        email=email,
        encrypted_pass=encrypted_password,
        salt=salt,
        validated_account=False
    )
    if not created_user:
        raise ValueError(f"Failed to register user: {email}")


def encrypt_password(plain_password: str) -> Tuple[str, str]:
    salt = get_random_salt()
    hashed_password = get_hex_digest(salt, plain_password)
    encrypted_password = f'{salt}${hashed_password}'
    return salt, encrypted_password


def get_hex_digest(salt: str, plain_password: str):
    return sha512(f'{salt}{plain_password}'.encode('utf-8')).hexdigest()


def get_random_salt() -> str:
    return sha512(f'{str(random())}{hash}'.encode('utf-8')).hexdigest()[:8]


def validate_password(plain_password: str, encrypted_password: str) -> bool:
    salt, hashed_password = encrypted_password.split('$')
    return hashed_password == get_hex_digest(salt, plain_password)
