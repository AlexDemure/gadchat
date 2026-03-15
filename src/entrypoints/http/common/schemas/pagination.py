import typing

from pydantic import BaseModel
from pydantic import Field


class Pagination(BaseModel):
    cursor: str | None = None
    limit: typing.Annotated[int, Field(gt=0, le=100)]


class Paginated(BaseModel):
    has_more: bool
    prev_cursor: str | None = None
    next_cursor: str | None = None
    items: list[typing.Any]
