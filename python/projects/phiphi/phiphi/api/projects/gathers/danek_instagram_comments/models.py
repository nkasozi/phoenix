"""Danek instagram comments gather model."""

from sqlalchemy import ForeignKey, orm

from phiphi.api import base_models
from phiphi.api.projects.gathers import models as gather_models


class DanekInstagramCommentsGather(gather_models.Gather):
    """Danek Instagram Posts Gather model."""

    __tablename__ = "danek_instagram_comments_gathers"
    __mapper_args__ = {
        "polymorphic_identity": "danek_instagram_comments",
    }

    id: orm.Mapped[int] = orm.mapped_column(ForeignKey("gathers.id"), primary_key=True)
    post_id_list: orm.Mapped[str] = orm.mapped_column(base_models.JSONEncodedValue)
    limit_comments_per_post: orm.Mapped[int]
    limit_child_comments_per_comment: orm.Mapped[int]
