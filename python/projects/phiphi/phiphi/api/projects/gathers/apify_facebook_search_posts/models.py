"""Apify facebook search posts gather model."""

from typing import Optional

from sqlalchemy import ForeignKey, orm

from phiphi.api import base_models
from phiphi.api.projects.gathers import models as gather_models


class ApifyFacebookSearchPostsGather(gather_models.Gather):
    """Apify Gather model."""

    __tablename__ = "apify_facebook_search_posts_gathers"
    __mapper_args__ = {
        "polymorphic_identity": "apify_facebook_search_posts",
    }

    id: orm.Mapped[int] = orm.mapped_column(ForeignKey("gathers.id"), primary_key=True)
    search_query: orm.Mapped[str]
    limit_posts: orm.Mapped[int]
    limit_retries: orm.Mapped[int]
    recent_posts: orm.Mapped[Optional[bool]]
    proxy: orm.Mapped[Optional[str]] = orm.mapped_column(base_models.JSONEncodedValue)
