"""Types for input schemas."""

from typing import Annotated

import pydantic

http_url_adapter = pydantic.TypeAdapter(pydantic.HttpUrl)

UrlStr = Annotated[
    str, pydantic.BeforeValidator(lambda value: str(http_url_adapter.validate_python(value)))
]
