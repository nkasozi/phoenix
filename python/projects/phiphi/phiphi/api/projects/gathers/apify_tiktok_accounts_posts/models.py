"""Apify TikTok Accounts posts gather model."""

from typing import Optional

from sqlalchemy import ForeignKey, orm

from phiphi.api import base_models
from phiphi.api.projects.gathers import models as gather_models


class ApifyTikTokAccountsPostsGather(gather_models.Gather):
    """Apify TikTok Accounts Posts Gather ORM model."""

    __tablename__ = "apify_tiktok_accounts_posts_gathers"
    __mapper_args__ = {
        "polymorphic_identity": "apify_tiktok_accounts_posts",
    }

    id: orm.Mapped[int] = orm.mapped_column(ForeignKey("gathers.id"), primary_key=True)
    limit_posts_per_account: orm.Mapped[int]
    account_username_list: orm.Mapped[str] = orm.mapped_column(base_models.JSONEncodedValue)
    posts_created_after: orm.Mapped[Optional[str]]
    posts_created_since_num_days: orm.Mapped[Optional[int]]
    proxy_country_to_gather_from: orm.Mapped[Optional[str]]
