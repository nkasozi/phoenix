"""Manual post authors ORModels."""

import sqlalchemy as sa
from sqlalchemy import orm

from phiphi import platform_db
from phiphi.api import base_models
from phiphi.api.projects.classifiers import models as classifiers_models


class IntermediatoryAuthorClassesBase(platform_db.Base):
    """Intermediatory author classes.

    The intermediatory table stores the "live" table, on which all edits and additions to
    the list of author classes are made.

    When a new version of the classifier is created, the table is copied to the
    "author_classes" attribute in the `params` of the classifier_versions table. Pipeline
    classifiers then use the versioned params to classify data.
    """

    __abstract__ = True

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    classifier_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("classifiers.id"))
    class_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("intermediatory_classes.id"))
    # This the author id from the project db
    phoenix_platform_message_author_id: orm.Mapped[str] = orm.mapped_column(
        sa.String, nullable=False
    )


class IntermediatoryAuthorClasses(IntermediatoryAuthorClassesBase, base_models.TimestampModel):
    """Intermediatory classified authors table."""

    __tablename__ = "intermediatory_author_classes"

    __table_args__ = (
        sa.UniqueConstraint(
            "classifier_id",
            "class_id",
            "phoenix_platform_message_author_id",
            name="uq_intermediatory_author_classes",
        ),
        sa.Index("ix_intermediatory_author_classes", "classifier_id", "class_id"),
        # We are adding an index on class_id to speed
        sa.Index("ix_intermediatory_author_classes_class_id", "class_id"),
        # We are adding an index on phoenix_platform_message_author_id as we are going to do a join
        # on this id from the project data
        sa.Index(
            "ix_intermediatory_author_classes_phoenix_id", "phoenix_platform_message_author_id"
        ),
    )

    # Define the relationship between IntermediatoryClassToKeywordConfig and IntermediatoryClasses
    intermediatory_class: orm.Mapped[classifiers_models.IntermediatoryClasses] = orm.relationship(
        "IntermediatoryClasses",
        back_populates="intermediatory_author_classes",
        lazy="selectin",  # Eager load the relationship as the class name is always needed
    )

    @property
    def class_name(self) -> str:
        """Retrieve the class name from the intermediatory_classes table."""
        return self.intermediatory_class.name
