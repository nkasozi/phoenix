"""Danek instagram posts gather model."""

from typing import Optional

from sqlalchemy import ForeignKey, orm

from phiphi.api import base_models
from phiphi.api.projects.gathers import models as gather_models


class DanekInstagramPostsGather(gather_models.Gather):
    """Danek Instagram Posts Gather model."""

    __tablename__ = "danek_instagram_posts_gathers"
    __mapper_args__ = {
        "polymorphic_identity": "danek_instagram_posts",
    }

    id: orm.Mapped[int] = orm.mapped_column(ForeignKey("gathers.id"), primary_key=True)
    limit_posts_per_account: orm.Mapped[int]
    account_username_list: orm.Mapped[str] = orm.mapped_column(base_models.JSONEncodedValue)
    posts_created_after: orm.Mapped[Optional[str]]
    scrape_comments_count_per_post: orm.Mapped[int]
    limit_child_comments_per_comment: orm.Mapped[int]
