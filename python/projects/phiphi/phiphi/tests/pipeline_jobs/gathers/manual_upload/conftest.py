"""Conftest manual_upload."""

import datetime

import pandas as pd

from phiphi.pipeline_jobs.gathers import manual_upload


def create_mock_manual_upload_df(num_rows=1):
    """Create a mock DataFrame that conforms to the manual_upload_schema."""
    input_df = pd.DataFrame(
        [
            {
                "platform": "facebook",
                "data_type": "posts",
                "message_id_pi": f"msg{i}",
                "message_author_id_pi": f"author{i}",
                "message_author_name_pi": f"Test Author {i}",
                "comment_replied_to_id_pi": None,
                "comment_parent_post_id_pi": None,
                "message_text_pi": f"Test message {i}",
                "message_url_pi": f"http://example.com/{i}",
                "message_datetime": datetime.datetime.utcnow(),
                "like_count": 10 + i,
                "share_count": 5 + i,
                "comment_count": 3 + i,
                "tiktok_post_plays": 2 + i,
                "x_post_retweeted_id": None,
                "x_is_quote": None,
                "x_is_reply": None,
            }
            for i in range(num_rows)
        ]
    )
    validation_result = manual_upload.manual_upload_schema.validate(input_df)
    return validation_result
