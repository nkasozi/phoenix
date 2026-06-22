"""Apify facebook comments gather model."""

from sqlalchemy import ForeignKey, orm

from phiphi.api import base_models
from phiphi.api.projects.gathers import models as gather_models


class ApifyFacebookCommentsGather(gather_models.Gather):
    """Apify Gather model."""

    __tablename__ = "apify_facebook_comments_gathers"
    __mapper_args__ = {
        "polymorphic_identity": "apify_facebook_comments",
    }

    id: orm.Mapped[int] = orm.mapped_column(ForeignKey("gathers.id"), primary_key=True)
    limit_comments_per_post: orm.Mapped[int]
    post_url_list: orm.Mapped[str] = orm.mapped_column(base_models.JSONEncodedValue)
    sort_comments_by: orm.Mapped[str]
    include_comment_replies: orm.Mapped[bool]
