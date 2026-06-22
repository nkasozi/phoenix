"""Apify tiktok comments gather model."""

from typing import Optional

from sqlalchemy import ForeignKey, orm

from phiphi.api import base_models
from phiphi.api.projects.gathers import models as gather_models


class ApifyTikTokCommentsGather(gather_models.Gather):
    """Apify Gather model."""

    __tablename__ = "apify_tiktok_comments_gathers"
    __mapper_args__ = {
        "polymorphic_identity": "apify_tiktok_comments",
    }

    id: orm.Mapped[int] = orm.mapped_column(ForeignKey("gathers.id"), primary_key=True)
    post_url_list: orm.Mapped[str] = orm.mapped_column(base_models.JSONEncodedValue)
    limit_total_comments: orm.Mapped[int]
    include_comment_replies: orm.Mapped[Optional[bool]]
