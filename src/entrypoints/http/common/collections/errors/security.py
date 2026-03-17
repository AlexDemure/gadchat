from src.common.http.collections.exceptions.error import Forbidden
from src.infrastructure.security.jwt.collections import TokenInvalid


AUTHORIZATION_ERRORS = [
    Forbidden,
    TokenInvalid,
]
