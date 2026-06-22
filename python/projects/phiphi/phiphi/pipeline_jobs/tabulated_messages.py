"""Tabulated messages table definition.

It is important that only table definitions are used for bigquery tables. This is due to bigquery
not supporting auto incrementing and applying constraints using a different DDL syntax. This is why
having a different syntax sqlalchemy-bigquery not supporting primary keys, indexes, and other table
constraints.

"""

import datetime

import pandas as pd
import sqlalchemy as sa

from phiphi import project_db
from phiphi.pipeline_jobs import constants, utils

tabulated_messages_table = sa.Table(
    constants.TABULATED_MESSAGES_TABLE_NAME,
    project_db.metadata,
    # General
    sa.Column("platform", sa.String, nullable=False),
    # Post Author
    sa.Column("post_author_category", sa.String, nullable=True),
    sa.Column("post_author_class", sa.String, nullable=True),
    sa.Column("post_author_description_pi", sa.Text, nullable=True),
    sa.Column("post_author_followers_count", sa.Integer, nullable=True),
    sa.Column("post_author_id", sa.String, nullable=False),
    sa.Column("post_author_location", sa.String, nullable=True),
    sa.Column("post_author_name_pi", sa.String, nullable=True),
    sa.Column("post_author_link_pi", sa.String, nullable=True),
    # Post
    sa.Column("post_class", sa.String, nullable=True),
    sa.Column("post_comment_count", sa.Integer, nullable=True),
    sa.Column("post_date", sa.Date, nullable=False),
    sa.Column("post_datetime", sa.TIMESTAMP, nullable=False),
    sa.Column("post_gather_id", sa.Integer, nullable=False),
    sa.Column("post_id", sa.String, nullable=False),
    sa.Column("post_like_count", sa.Integer, nullable=True),
    sa.Column("post_link_pi", sa.String, nullable=True),
    sa.Column("post_share_count", sa.Integer, nullable=True),
    sa.Column("post_text_pi", sa.Text, nullable=True),
    sa.Column("post_message_id_pi", sa.Text, nullable=True),
    # Comments author
    sa.Column("comment_author_class", sa.String, nullable=True),
    sa.Column("comment_author_id", sa.String, nullable=False),
    sa.Column("comment_author_name_pi", sa.String, nullable=True),
    # Comments
    sa.Column("comment_class", sa.String, nullable=True),
    sa.Column("comment_date", sa.Date, nullable=False),
    sa.Column("comment_datetime", sa.TIMESTAMP, nullable=False),
    sa.Column("comment_gather_id", sa.Integer, nullable=False),
    sa.Column("comment_id", sa.String, nullable=False),
    sa.Column("comment_like_count", sa.Integer, nullable=True),
    sa.Column("comment_link_pi", sa.String, nullable=True),
    sa.Column("comment_parent_post_id", sa.String, nullable=False),
    sa.Column("comment_replied_to_id", sa.String, nullable=True),
    sa.Column("comment_text_pi", sa.Text, nullable=True),
    # Platform specific
    sa.Column("facebook_video_views", sa.Integer, nullable=True),
    sa.Column("tiktok_post_plays", sa.Integer, nullable=True),
    sa.Column("x_post_retweeted_id", sa.String, nullable=True),
    sa.Column("x_comment_is_quote", sa.Boolean, nullable=True),
    sa.Column("x_comment_is_reply", sa.Boolean, nullable=True),
    # Add columns here
    # Developer columns should always go last
    # Pandas datetime is parsed into Bigquery as TIMESTAMP by default
    sa.Column("phoenix_processed_at", sa.TIMESTAMP, nullable=False),
    sa.Column("phoenix_job_run_id", sa.Integer, nullable=False),
)


def seed_dummy_data(project_namespace: str) -> None:
    """Seed the tabulated messages table with dummy data.

    Args:
        project_namespace (str): The project namespace.
    """
    seed_tabulated_dummy_df = pd.DataFrame(
        [
            {
                "platform": "dummy_platform",
                "post_author_category": "dummy_category",
                "post_author_class": "dummy_class",
                "post_author_description_pi": "dummy_description",
                "post_author_followers_count": 100,
                "post_author_id": "dummy_author_id",
                "post_author_location": "dummy_location",
                "post_author_name_pi": "dummy_name",
                "post_author_link_pi": "dummy_link",
                "post_class": "dummy_class",
                "post_comment_count": 100,
                "post_date": datetime.date.today(),
                "post_datetime": datetime.datetime.now(),
                "post_gather_id": 1,
                "post_id": "dummy_post_id",
                "post_like_count": 100,
                "post_link_pi": "dummy_link",
                "post_share_count": 100,
                "post_text_pi": "dummy_text",
                "comment_author_class": "class",
                "comment_author_id": "dummy_comment_id",
                "comment_author_name_pi": "name",
                "comment_class": "dummy_class",
                "comment_date": datetime.date.today(),
                "comment_datetime": datetime.datetime.now(),
                "comment_gather_id": 1,
                "comment_id": "1",
                "comment_like_count": 100,
                "comment_link_pi": "dummy_link",
                "comment_parent_post_id": "dummy_post_id",
                "comment_replied_to_id": "dummy_comment_id",
                "comment_text_pi": "dummy_text",
                "facebook_video_views": 100,
                "tiktok_post_plays": 0,
                "x_post_retweeted_id": None,
                "x_comment_is_quote": None,
                "x_comment_is_reply": None,
                "phoenix_processed_at": datetime.datetime.now(),
                "phoenix_job_run_id": 0,
            },
            {
                "platform": "dummy_platform",
                "post_author_category": "dummy_category",
                "post_author_class": "dummy_class",
                "post_author_description_pi": "dummy_description",
                "post_author_followers_count": 100,
                "post_author_id": "dummy_author_id",
                "post_author_location": "dummy_location",
                "post_author_name_pi": "dummy_name",
                "post_author_link_pi": "dummy_link",
                "post_class": "dummy_class",
                "post_comment_count": 100,
                "post_date": datetime.date.today(),
                "post_datetime": datetime.datetime.now(),
                "post_gather_id": 1,
                "post_id": "dummy_post_id",
                "post_like_count": 100,
                "post_link_pi": "dummy_link",
                "post_share_count": 100,
                "post_text_pi": "dummy_text",
                "comment_author_class": "class",
                "comment_author_id": "dummy_comment_id",
                "comment_author_name_pi": "name",
                "comment_class": "dummy_class",
                "comment_date": datetime.date.today(),
                "comment_datetime": datetime.datetime.now(),
                "comment_gather_id": 1,
                "comment_id": "1",
                "comment_like_count": 100,
                "comment_link_pi": "dummy_link",
                "comment_parent_post_id": "dummy_post_id",
                "comment_replied_to_id": "dummy_comment_id",
                "comment_text_pi": "dummy_text",
                "facebook_video_views": 0,
                "tiktok_post_plays": 100,
                "x_post_retweeted_id": None,
                "x_comment_is_quote": None,
                "x_comment_is_reply": None,
                "phoenix_processed_at": datetime.datetime.now(),
                "phoenix_job_run_id": 0,
            },
        ],
    )
    utils.write_data(
        seed_tabulated_dummy_df,
        project_namespace,
        constants.TABULATED_MESSAGES_TABLE_NAME,
        with_rate_limit=False,
    )
