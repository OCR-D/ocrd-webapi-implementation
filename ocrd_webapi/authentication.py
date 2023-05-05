from hashlib import sha512
from random import random
from typing import Tuple

from .database import create_user, get_user


async def authenticate_user(email: str, password: str):
    db_user = await get_user(email=email)
    if not db_user:
        raise ValueError(f"User not found: {email}")
    password_status = validate_password(
        plain_password=password,
        encrypted_password=db_user.encrypted_pass
    )
    if not password_status:
        raise ValueError(f"Wrong credentials! User was not validated: {email}")
    if not db_user.validated_user:
        raise ValueError(f"The account was not validated by an admin account!")


async def register_user(email: str, password: str, validated_account=False):
    salt, encrypted_password = encrypt_password(password)
    db_user = await get_user(email)
    if db_user:
        raise ValueError(f"User is already registered: {email}")
    created_user = await create_user(
        email=email,
        encrypted_pass=encrypted_password,
        salt=salt,
        validated_account=validated_account
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
    return sha512(f'{hash(str(random()))}'.encode('utf-8')).hexdigest()[:8]


def validate_password(plain_password: str, encrypted_password: str) -> bool:
    salt, hashed_password = encrypted_password.split('$', 1)
    return hashed_password == get_hex_digest(salt, plain_password)
