import typing

from pydantic import Field
from pydantic import StringConstraints


StrRef = typing.Annotated[
    str,
    StringConstraints(
        to_lower=True,
        min_length=1,
        max_length=256,
        strip_whitespace=True,
    ),
]
