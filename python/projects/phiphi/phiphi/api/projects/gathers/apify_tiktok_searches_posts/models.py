"""Apify TikTok Searches posts gather model."""

from typing import Optional

from sqlalchemy import ForeignKey, orm

from phiphi.api import base_models
from phiphi.api.projects.gathers import models as gather_models


class ApifyTikTokSearchesPostsGather(gather_models.Gather):
    """Apify TikTok Searches Posts Gather ORM model."""

    __tablename__ = "apify_tiktok_searches_posts_gathers"
    __mapper_args__ = {
        "polymorphic_identity": "apify_tiktok_searches_posts",
    }

    id: orm.Mapped[int] = orm.mapped_column(ForeignKey("gathers.id"), primary_key=True)
    limit_posts_per_search: orm.Mapped[int]
    search_list: orm.Mapped[str] = orm.mapped_column(base_models.JSONEncodedValue)
    proxy_country_to_gather_from: orm.Mapped[Optional[str]]
