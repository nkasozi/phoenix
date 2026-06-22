"""Base models.

This module contains the base models that are used by other
models in the application.

Usage:
    The models in this module are not meant to be used directly.
    Instead, they are meant to be inherited by other models.

    ```python
    class MyModel(MyBaseModel, base_models.TimestampModel):
        pass
    ```

    The above example shows how to inherit from the TimestampModel.
    Using base models in this way allows for easy reuse of common fields.
"""

import datetime
import json

from sqlalchemy import orm
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import VARCHAR, TypeDecorator

from phiphi import platform_db


class TimestampModel(platform_db.Base):
    """Time stamp columns to be used as a base."""

    __abstract__ = True

    created_at: orm.Mapped[datetime.datetime] = orm.mapped_column(
        # When we want to test the created_at we have to use the lambda
        # https://github.com/spulec/freezegun/issues/306
        default=lambda: datetime.datetime.now()
    )
    updated_at: orm.Mapped[datetime.datetime] = orm.mapped_column(
        default=lambda: datetime.datetime.now(), onupdate=lambda: datetime.datetime.now()
    )


class JSONEncodedValue(TypeDecorator):
    """A custom type for encoding and decoding values as JSON.

    This type is used to store JSON data in the database. The pydantic model can have a fields with
    a type of dict or list and this type will handle the conversion to and from the database.

    Usage:
        ```python
        class MyModel(platform_db.Base):
            __tablename__ = "my_table"

            id orm.Mapped[int] = orm.mapped_column(primary_key=True)
            data orm.Mapped[str] = orm.mapped_column(JSONEncodedValue)
        ```

        The above example shows how to use the JSONEncodedValue type in a model.
    """

    impl = VARCHAR

    def process_bind_param(self, value: dict | list | None, dialect: Dialect) -> str | None:
        """Process the value before it is written to the database."""
        result = None
        if value is not None:
            result = json.dumps(value)
        return result

    def process_result_value(self, value: str | None, dialect: Dialect) -> dict | list | None:
        """Process the value after it is read from the database."""
        result = None
        if value is not None:
            result = json.loads(value)
        return result
