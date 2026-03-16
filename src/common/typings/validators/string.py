import typing

from pydantic import StringConstraints


String = typing.Annotated[str, StringConstraints(min_length=1, max_length=2048, strip_whitespace=True)]
Search = typing.Annotated[str, StringConstraints(to_lower=True, min_length=1, max_length=256, strip_whitespace=True)]
