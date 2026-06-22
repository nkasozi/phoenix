"""Base schemas."""

import pydantic


class ListMeta(pydantic.BaseModel):
    """List meta schema."""

    total_count: int = pydantic.Field(..., description="The total count of items.")
    start_index: int = pydantic.Field(..., description="The start index.")
    end_index: int = pydantic.Field(..., description="The end index.")
