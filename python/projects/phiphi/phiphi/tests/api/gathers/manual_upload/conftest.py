"""Shared fixtures for testing manual upload."""

import pandas as pd

from phiphi.pipeline_jobs import generalised_messages


def create_valid_manual_upload_df(num_rows=1):
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
                "message_datetime": f"2023-01-01 00:00:{i:02d}",
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
    input_df = generalised_messages.coerce_optional_values(input_df)
    return input_df
