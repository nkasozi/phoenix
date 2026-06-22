"""Apify TikTok Hashtags posts gather model."""

from typing import Optional

from sqlalchemy import ForeignKey, orm

from phiphi.api import base_models
from phiphi.api.projects.gathers import models as gather_models


class ApifyTikTokHashtagsPostsGather(gather_models.Gather):
    """Apify TikTok Hashtags Posts Gather ORM model."""

    __tablename__ = "apify_tiktok_hashtags_posts_gathers"
    __mapper_args__ = {
        "polymorphic_identity": "apify_tiktok_hashtags_posts",
    }

    id: orm.Mapped[int] = orm.mapped_column(ForeignKey("gathers.id"), primary_key=True)
    limit_posts_per_hashtag: orm.Mapped[int]
    hashtag_list: orm.Mapped[str] = orm.mapped_column(base_models.JSONEncodedValue)
    proxy_country_to_gather_from: orm.Mapped[Optional[str]]
