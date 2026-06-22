"""Danek facebook searches posts gather model."""

from typing import Optional

from sqlalchemy import ForeignKey, orm

from phiphi.api import base_models
from phiphi.api.projects.gathers import models as gather_models


class DanekFacebookSearchesPostsGather(gather_models.Gather):
    """Danek Facebook Searches Posts Gather model."""

    __tablename__ = "danek_facebook_searches_posts_gathers"
    __mapper_args__ = {
        "polymorphic_identity": "danek_facebook_searches_posts",
    }

    id: orm.Mapped[int] = orm.mapped_column(ForeignKey("gathers.id"), primary_key=True)
    stop_scraping_per_search_after_count: orm.Mapped[int]
    search_list: orm.Mapped[str] = orm.mapped_column(base_models.JSONEncodedValue)
    proxy_country_to_gather_from: orm.Mapped[Optional[str]]
    posts_created_after: orm.Mapped[Optional[str]]
    posts_created_before: orm.Mapped[Optional[str]]
    recent_posts: orm.Mapped[bool]
