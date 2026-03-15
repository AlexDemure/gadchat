from pydantic import BaseModel


class Signature(BaseModel):
    sub: str
    exp: int
    jti: str


class Token(BaseModel):
    token: str
