"""Models for classifiers and classifier versions tables."""

import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import orm

from phiphi import platform_db
from phiphi.api import base_models
from phiphi.api.projects.job_runs import models as job_run_models
from phiphi.api.projects.job_runs import schemas as job_run_schemas


class ClassifierVersionsBase(platform_db.Base):
    """Classifier versions table."""

    __abstract__ = True

    __tablename__ = "classifier_versions"

    version_id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    classifier_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("classifiers.id"))
    classes: orm.Mapped[str] = orm.mapped_column(base_models.JSONEncodedValue)
    params: orm.Mapped[Optional[str]] = orm.mapped_column(base_models.JSONEncodedValue)


class ClassifierVersions(ClassifierVersionsBase, base_models.TimestampModel):
    """Classifier versions table."""

    __tablename__ = "classifier_versions"


class ClassifiersBase(platform_db.Base):
    """Classifiers model."""

    __abstract__ = True

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    project_id: orm.Mapped[int]
    name: orm.Mapped[str]
    description: orm.Mapped[str]
    type: orm.Mapped[str]
    archived_at: orm.Mapped[datetime.datetime | None] = orm.mapped_column(nullable=True)
    last_edited_at: orm.Mapped[datetime.datetime | None] = orm.mapped_column(nullable=True)


job_run_foreign_type_query = (
    "or_("
    f"JobRuns.foreign_job_type=='{job_run_schemas.ForeignJobType.classify.value}',"
    f"JobRuns.foreign_job_type=='{job_run_schemas.ForeignJobType.classify_tabulate.value}',"
    f"JobRuns.foreign_job_type=='{job_run_schemas.ForeignJobType.classifier_archive.value}',"
    f"JobRuns.foreign_job_type=='{job_run_schemas.ForeignJobType.classifier_restore.value}'"
    ")"
)


class Classifiers(ClassifiersBase, base_models.TimestampModel):
    """Classifiers table."""

    __tablename__ = "classifiers"

    # Relationship to ClassifierVersions
    classifier_versions: orm.Mapped[list[ClassifierVersions]] = orm.relationship(
        "ClassifierVersions",
        cascade="all, delete-orphan",
        order_by="ClassifierVersions.version_id.desc()",  # Ensures ordered by desc version_id
        # For all response types we need the latest version so this will be eager loaded
        lazy="selectin",
    )

    intermediatory_classes = orm.relationship(
        "IntermediatoryClasses",
        cascade="all, delete-orphan",
        order_by="IntermediatoryClasses.id",
        lazy="select",
    )

    intermediatory_class_to_keyword_configs = orm.relationship(
        "IntermediatoryClassToKeywordConfig",
        cascade="all, delete-orphan",
        # Order by class_id and id to ensure that the order is consistent
        # And so that for the user it matches the ordering of intermediatory_classes
        order_by="asc(IntermediatoryClassToKeywordConfig.class_id),asc(IntermediatoryClassToKeywordConfig.id)",
        lazy="select",
    )

    intermediatory_author_classes = orm.relationship(
        "IntermediatoryAuthorClasses",
        cascade="all, delete-orphan",
        order_by="asc(IntermediatoryAuthorClasses.id)",
        lazy="select",
    )

    # Relationship to get all related JobRuns, ordered by id descending
    # Using a selectin relationship so that we avoid the N+1 query problem for a list of
    # classifiers
    job_runs: orm.Mapped[list[job_run_models.JobRuns]] = orm.relationship(
        "JobRuns",
        order_by="desc(JobRuns.id)",
        primaryjoin=(
            f"and_({job_run_foreign_type_query}, foreign(JobRuns.foreign_id)==Classifiers.id)"
        ),
        lazy="selectin",
    )

    @property
    def latest_version(self) -> ClassifierVersions | None:
        """Get the latest version of the classifier."""
        if len(self.classifier_versions) == 0:
            return None
        return self.classifier_versions[0]

    def all_versions(self) -> list[ClassifierVersions]:
        """Get all versions of the classifier."""
        return self.classifier_versions

    @property
    def latest_job_run(self) -> job_run_models.JobRuns | None:
        """Property to get the most recent JobRun."""
        if not self.job_runs:
            return None

        return self.job_runs[0]  # First item (already ordered by desc)


class IntermediatoryClassesBase(platform_db.Base):
    """Intermediatory classes table base.

    The intermediatory classes table stores the "live" table, on which all edits and additions to
    the classes are applied to.

    When a new version of the classifier is created, the classes are copied from this table to the
    classifier_versions table.
    """

    __abstract__ = True

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    classifier_id: orm.Mapped[int] = orm.mapped_column(sa.ForeignKey("classifiers.id"))
    name: orm.Mapped[str]
    description: orm.Mapped[str]


class IntermediatoryClasses(IntermediatoryClassesBase, base_models.TimestampModel):
    """Intermediatory classes table."""

    __tablename__ = "intermediatory_classes"

    __table_args__ = (
        sa.UniqueConstraint("classifier_id", "name", name="uq_classifier_classname"),
        sa.Index("ix_classifier_classname", "classifier_id", "name"),
    )

    intermediatory_class_to_keyword_configs = orm.relationship(
        "IntermediatoryClassToKeywordConfig",
        back_populates="intermediatory_class",
        cascade="all, delete-orphan",
        order_by="asc(IntermediatoryClassToKeywordConfig.id)",
        lazy="select",
    )
    intermediatory_author_classes = orm.relationship(
        "IntermediatoryAuthorClasses",
        back_populates="intermediatory_class",
        cascade="all, delete-orphan",
        order_by="asc(IntermediatoryAuthorClasses.id)",
        lazy="select",
    )
