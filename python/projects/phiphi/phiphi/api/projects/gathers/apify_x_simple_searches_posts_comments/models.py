"""Apify X Simple Searches → Posts+Comments gather model."""

from typing import List, Optional

from sqlalchemy import ForeignKey, orm

from phiphi.api import base_models
from phiphi.api.projects.gathers import models as gather_models


class ApifyXSimpleSearchesPostsCommentsGather(gather_models.Gather):
    """SQLAlchemy model for Apify X simple searches (posts+comments).

    This model stores the configuration needed to run Apify actor(s) that scrape
    X (Twitter) using simple keyword and handle searches and collect posts with
    their comments. The shape mirrors the pydantic schemas in `schemas.py`.

    `search_list` is an instance attribute even though it is computed as it simplifies the code to
    store the pydantic instance.
    """

    __tablename__ = "apify_x_simple_searches_posts_comments_gathers"
    __mapper_args__ = {
        "polymorphic_identity": "apify_x_simple_searches_posts_comments",
    }

    id: orm.Mapped[int] = orm.mapped_column(ForeignKey("gathers.id"), primary_key=True)
    handle_list: orm.Mapped[List[str]] = orm.mapped_column(base_models.JSONEncodedValue)
    keywords_list: orm.Mapped[List[str]] = orm.mapped_column(base_models.JSONEncodedValue)
    limit_results_per_search: orm.Mapped[int]
    posts_created_after: orm.Mapped[Optional[str]]
    posts_created_before: orm.Mapped[Optional[str]]
    sort: orm.Mapped[Optional[str]]
    location_near: orm.Mapped[Optional[str]]
    search_list: orm.Mapped[List[str]] = orm.mapped_column(base_models.JSONEncodedValue)
