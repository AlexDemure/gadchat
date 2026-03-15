import jwt

from src.common.formats.utils import date
from src.common.formats.utils import uuid
from src.configuration import settings

from .collections import TokenInvalid
from .models import Signature
from .models import Token


class JWT:
    @classmethod
    def encode(cls, subject: str) -> Token:
        payload = Signature(
            sub=subject,
            exp=int(date.shift(seconds=settings.JWT_EXPIRED_SECONDS).timestamp()),
            jti=uuid.unique(),
        ).model_dump()
        return Token(token=jwt.encode(payload=payload, key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM))

    @classmethod
    def decode(cls, token: str) -> Signature:
        try:
            return Signature(**jwt.decode(token, key=settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]))
        except jwt.PyJWTError:
            raise TokenInvalid
