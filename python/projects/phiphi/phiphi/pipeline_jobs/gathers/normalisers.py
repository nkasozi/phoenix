"""Functions which take an Apify json blob and normalise it into a standard format."""

import hashlib
import uuid
from datetime import datetime
from typing import Dict, Union

from phiphi.api.projects.gathers import schemas as gathers_schemas


def anonymize(input_value: Union[str, int]) -> str:
    """Generate a UUID hash from a given input value - for anonymization."""
    return str(uuid.UUID(hashlib.md5(str(input_value).encode()).hexdigest()))


def is_apify_scraping_error(json_blob: Dict) -> bool:
    """When apify's scraping fails, it returns a json blob with an 'error' key.

    This is undocumented, but we've seen that blobs have an "error" key, with differing extra
    keys depending on the scraper.
    """
    if "error" in json_blob:
        return True
    return False


def is_empty_result(json_blob: Dict) -> bool:
    """When apify's scraping returns an empty result, it can return a json blob without an id key.

    This is undocumented, but we've seen that tiktok results return "authorMeta" data without
    any messages if the user hasn't posted in the timeframe of the scrape.
    """
    if "id" not in json_blob:
        return True
    return False


def normalise_to_int(value: str | int | None) -> int:
    """Normalise a string or int to an int, handling suffixes like k, m, b. If None, return 0."""
    if not value:
        return 0
    if isinstance(value, int):
        return value
    suffixes = dict(k=1e3, m=1e6, b=1e9)
    if value[-1].lower() in suffixes:
        factor, exp = value[0:-1], value[-1].lower()
        ans = int(float(factor) * suffixes[exp])
    else:
        ans = int(value)
    return ans


def add_optional_fields(record: dict) -> dict:
    """Add optional fields to a normalized record if they are missing."""
    optional_fields = [
        "tiktok_post_plays",
        "x_post_retweeted_id",
        "x_is_quote",
        "x_is_reply",
    ]
    for field in optional_fields:
        if field not in record:
            record[field] = None
    return record


def normalise_single_manual_upload_json(json_blob: Dict) -> Dict | None:
    """Extract fields from a single manual upload JSON blob to normalized form."""
    phoenix_platform_parent_message_id: str | None = None
    if json_blob.get("comment_replied_to_id_pi"):
        phoenix_platform_parent_message_id = anonymize(json_blob["comment_replied_to_id_pi"])

    phoenix_platform_root_message_id: str | None = None
    if json_blob.get("comment_parent_post_id_pi"):
        phoenix_platform_root_message_id = anonymize(json_blob["comment_parent_post_id_pi"])
    return {
        # These are only in the manual upload data
        "platform": json_blob["platform"],
        "data_type": json_blob["data_type"],
        # These are common to other normalisers
        "pi_platform_message_id": json_blob["message_id_pi"],
        "pi_platform_message_author_id": json_blob["message_author_id_pi"],
        "pi_platform_message_author_name": json_blob["message_author_name_pi"],
        "pi_platform_parent_message_id": json_blob["comment_replied_to_id_pi"],
        "pi_platform_root_message_id": json_blob["comment_parent_post_id_pi"],
        "pi_text": json_blob["message_text_pi"],
        "pi_platform_message_url": json_blob["message_url_pi"],
        "platform_message_last_updated_at": datetime.fromisoformat(json_blob["message_datetime"]),
        "phoenix_platform_message_id": anonymize(json_blob["message_id_pi"]),
        "phoenix_platform_message_author_id": anonymize(json_blob["message_author_id_pi"]),
        "phoenix_platform_parent_message_id": phoenix_platform_parent_message_id,
        "phoenix_platform_root_message_id": phoenix_platform_root_message_id,
        "like_count": json_blob["like_count"],
        "share_count": json_blob["share_count"],
        "comment_count": json_blob["comment_count"],
        "tiktok_post_plays": json_blob["tiktok_post_plays"],
        "x_post_retweeted_id": json_blob.get("x_post_retweeted_id"),
        "x_is_quote": json_blob.get("x_is_quote"),
        "x_is_reply": json_blob.get("x_is_reply"),
    }


def normalise_single_facebook_posts_json(json_blob: Dict) -> Dict | None:
    """Extract fields from a single Facebook post JSON blob to normalized form."""
    if is_apify_scraping_error(json_blob):
        return None

    result = {
        "pi_platform_message_id": json_blob["postId"],
        "pi_platform_message_author_id": json_blob["user"]["id"],
        "pi_platform_message_author_name": json_blob["user"]["name"],
        "pi_platform_parent_message_id": None,  # Posts don't have parent messages
        "pi_platform_root_message_id": None,  # Posts don't have root messages
        "pi_text": json_blob["text"],
        "pi_platform_message_url": json_blob["url"],
        "platform_message_last_updated_at": datetime.fromisoformat(json_blob["time"]),
        "phoenix_platform_message_id": anonymize(json_blob["postId"]),
        "phoenix_platform_message_author_id": anonymize(json_blob["user"]["id"]),
        "phoenix_platform_parent_message_id": None,  # Posts don't have parent messages
        "phoenix_platform_root_message_id": None,  # Posts don't have root messages
        # stats
        "like_count": normalise_to_int(json_blob.get("likes", 0)),
        "share_count": normalise_to_int(json_blob.get("shares", 0)),
        "comment_count": normalise_to_int(json_blob.get("comments", 0)),
    }
    return add_optional_fields(result)


def normalise_single_facebook_search_posts_json(json_blob: Dict) -> Dict | None:
    """Extract fields from a single Facebook search post JSON blob to normalized form."""
    if is_apify_scraping_error(json_blob):
        return None

    if "post_id" not in json_blob and "message" in json_blob:
        # This means there was some error
        return None

    like_count = 0
    # There is a chance that reactions is not in the json_blob
    if "reactions" in json_blob:
        like_count = normalise_to_int(json_blob["reactions"].get("like", 0))

    result = {
        "pi_platform_message_id": json_blob["post_id"],
        "pi_platform_message_author_id": json_blob["author"]["id"],
        "pi_platform_message_author_name": json_blob["author"]["name"],
        "pi_platform_parent_message_id": None,  # Posts don't have parent messages
        "pi_platform_root_message_id": None,  # Posts don't have root messages
        "pi_text": json_blob["message"],
        "pi_platform_message_url": json_blob["url"],
        "platform_message_last_updated_at": datetime.utcfromtimestamp(json_blob["timestamp"]),
        "phoenix_platform_message_id": anonymize(json_blob["post_id"]),
        "phoenix_platform_message_author_id": anonymize(json_blob["author"]["id"]),
        "phoenix_platform_parent_message_id": None,  # Posts don't have parent messages
        "phoenix_platform_root_message_id": None,  # Posts don't have root messages
        # stats
        "like_count": like_count,
        "share_count": 0,  # Facebook search posts don't have shares
        "comment_count": normalise_to_int(json_blob.get("comments_count", 0)),
    }
    return add_optional_fields(result)


def normalise_single_facebook_comments_json(json_blob: Dict) -> Dict | None:
    """Extract fields from a single Facebook comment JSON blob to normalized form."""
    if is_apify_scraping_error(json_blob):
        return None
    # Sometimes the Apify actor's GraphQL API returns what seems to be an empty node, with
    # only the post url, and `"video_home_www_trending_hashtag":[]` as the only key-value pairs.
    if "id" not in json_blob:
        return None

    if "replyToCommentId" in json_blob:
        parent_message_id = json_blob["replyToCommentId"]
    else:
        parent_message_id = json_blob["facebookId"]

    result = {
        "pi_platform_message_id": json_blob["id"],
        "pi_platform_message_author_id": json_blob["profileId"],
        "pi_platform_message_author_name": json_blob["profileName"],
        "pi_platform_parent_message_id": parent_message_id,
        "pi_platform_root_message_id": json_blob["facebookId"],
        "pi_text": json_blob.get("text", ""),
        "pi_platform_message_url": json_blob["commentUrl"],
        "platform_message_last_updated_at": datetime.fromisoformat(json_blob["date"]),
        "phoenix_platform_message_id": anonymize(json_blob["id"]),
        "phoenix_platform_message_author_id": anonymize(json_blob["profileId"]),
        "phoenix_platform_parent_message_id": anonymize(parent_message_id),
        "phoenix_platform_root_message_id": anonymize(json_blob["facebookId"]),
        # stats
        "like_count": normalise_to_int(json_blob.get("likesCount", 0)),
        # There are no shares of comments for facebook
        "share_count": 0,
        "comment_count": normalise_to_int(json_blob.get("commentsCount", 0)),
    }
    return add_optional_fields(result)


def normalise_single_tiktok_posts_json(json_blob: Dict) -> Dict | None:
    """Extract fields from a single TikTok post JSON blob to normalized form.

    This normaliser can be used for all gathers that use the clockwork/tiktok-scraper with the
    `searchSection` input as `/video`. Ref:
    https://apify.com/clockworks/tiktok-scraper/input-schema
    """
    if is_apify_scraping_error(json_blob):
        return None
    if is_empty_result(json_blob):
        return None

    result = {
        "pi_platform_message_id": json_blob["id"],
        "pi_platform_message_author_id": json_blob["authorMeta"]["id"],
        "pi_platform_message_author_name": json_blob["authorMeta"]["name"],
        "pi_platform_parent_message_id": None,
        "pi_platform_root_message_id": None,
        "pi_text": json_blob["text"],
        "pi_platform_message_url": json_blob["webVideoUrl"],
        "platform_message_last_updated_at": datetime.fromisoformat(json_blob["createTimeISO"]),
        "phoenix_platform_message_id": anonymize(json_blob["id"]),
        "phoenix_platform_message_author_id": anonymize(json_blob["authorMeta"]["id"]),
        "phoenix_platform_parent_message_id": None,
        "phoenix_platform_root_message_id": None,
        # stats
        "like_count": normalise_to_int(json_blob.get("diggCount", 0)),
        "share_count": normalise_to_int(json_blob.get("shareCount", 0)),
        "comment_count": normalise_to_int(json_blob.get("commentCount", 0)),
        "tiktok_post_plays": normalise_to_int(json_blob.get("playCount", 0)),
    }
    return add_optional_fields(result)


def normalise_single_tiktok_comments_json(json_blob: Dict) -> Dict | None:
    """Extract fields from a single TikTok comment JSON blob to normalized form.

    This normaliser can be used for all gathers that use the apidojo/tiktok-comments-scraper actor.
    https://apify.com/apidojo/tiktok-comments-scraper/input-schema
    """
    # Tiktok comments have a "noResults" key if there are no comments for a post
    if "noResults" in json_blob and json_blob["noResults"] is True:
        return None

    # ParentId is the comment of a reply and is not set if it is a top-level comment
    parent_message_id = json_blob.get("parentId", json_blob["awemeId"])

    # Check that user data is present
    user = json_blob.get("user")
    if not user or "id" not in user:
        return None

    user_id = user.get("id").strip()
    if not user_id:
        return None

    username = user.get("username", "").strip()

    # User id acts the same as username for https://www.tiktok.com/@<user_id>
    if not username:
        username = user_id

    result = {
        "pi_platform_message_id": json_blob["id"],
        "pi_platform_message_author_id": json_blob["user"]["id"],
        "pi_platform_message_author_name": username,
        "pi_platform_parent_message_id": parent_message_id,
        "pi_platform_root_message_id": json_blob["awemeId"],
        "pi_text": json_blob["text"],
        # Tiktok has no url for comments
        "pi_platform_message_url": None,
        "platform_message_last_updated_at": datetime.fromisoformat(json_blob["createdAt"]),
        "phoenix_platform_message_id": anonymize(json_blob["id"]),
        "phoenix_platform_message_author_id": anonymize(json_blob["user"]["id"]),
        "phoenix_platform_parent_message_id": anonymize(parent_message_id),
        "phoenix_platform_root_message_id": anonymize(json_blob["awemeId"]),
        "like_count": normalise_to_int(json_blob.get("likeCount", 0)),
        # No shares for TikTok comments
        "share_count": 0,
        "comment_count": normalise_to_int(json_blob.get("replyCount", 0)),
    }
    return add_optional_fields(result)


def normalise_single_x_advanced_searches_posts_comments_json(json_blob: Dict) -> Dict | None:
    """Extract fields from a single X/Twitter advanced search JSON blob to normalized form.

    Handles both posts and comments (replies/quotes) from X/Twitter data.

    Priority hierarchy:
    1. Reply (becomes comment with inReplyToId as parent)
    2. Quote (becomes comment + extracts quoted tweet as post)
    3. Retweet (becomes post + extracts retweeted tweet as post)
    4. Regular post (no relationships)
    """
    if is_apify_scraping_error(json_blob):
        return None

    if "id" not in json_blob:
        return None

    is_reply = json_blob.get("isReply", False)
    is_quote = json_blob.get("isQuote", False)
    is_retweet = json_blob.get("isRetweet", False)

    tweet_id = json_blob["id"]
    conversation_id = json_blob.get("conversationId")

    if is_reply:
        data_type = gathers_schemas.DataType.comments.value
        parent_message_id = json_blob.get("inReplyToId")
        root_message_id = conversation_id if conversation_id != tweet_id else None
        x_post_retweeted_id = None

    elif is_quote:
        data_type = gathers_schemas.DataType.comments.value
        quote_data = json_blob.get("quote", {})
        parent_message_id = quote_data.get("id") if quote_data else None
        root_message_id = conversation_id if conversation_id != tweet_id else None
        x_post_retweeted_id = None

    elif is_retweet:
        data_type = gathers_schemas.DataType.posts.value
        retweet_data = json_blob.get("retweet", {})
        retweeted_tweet_id = retweet_data.get("id") if retweet_data else None
        parent_message_id = None
        root_message_id = None
        x_post_retweeted_id = retweeted_tweet_id

    else:
        data_type = gathers_schemas.DataType.posts.value
        parent_message_id = None
        root_message_id = None
        x_post_retweeted_id = None

    author = json_blob.get("author", {})
    # If there is no author data or no author id, we cannot process this record as it is essential
    # for our data model and anonymization.
    if author is None or "id" not in author:
        return None

    username = author.get("userName", author.get("id"))

    result = {
        "pi_platform_message_id": json_blob["id"],
        "pi_platform_message_author_id": author.get("id"),
        "pi_platform_message_author_name": username,
        "pi_platform_parent_message_id": parent_message_id,
        "pi_platform_root_message_id": root_message_id,
        "pi_text": json_blob.get("fullText", json_blob.get("text", "")),
        "pi_platform_message_url": json_blob.get("url"),
        "platform_message_last_updated_at": datetime.strptime(
            json_blob["createdAt"], "%a %b %d %H:%M:%S %z %Y"
        ),
        "phoenix_platform_message_id": anonymize(json_blob["id"]),
        "phoenix_platform_message_author_id": anonymize(author.get("id")),
        "phoenix_platform_parent_message_id": anonymize(parent_message_id)
        if parent_message_id
        else None,
        "phoenix_platform_root_message_id": anonymize(root_message_id)
        if root_message_id
        else None,
        "like_count": normalise_to_int(json_blob.get("likeCount", 0)),
        "share_count": normalise_to_int(json_blob.get("retweetCount", 0)),
        "comment_count": (
            normalise_to_int(json_blob.get("quoteCount", 0))
            + normalise_to_int(json_blob.get("replyCount", 0))
        ),
        "tiktok_post_plays": None,
        "platform": gathers_schemas.Platform.x.value,
        "data_type": data_type,
        "x_post_retweeted_id": x_post_retweeted_id,
        "x_is_quote": is_quote,
        "x_is_reply": is_reply,
    }

    return add_optional_fields(result)


def extract_retweeted_tweet_as_post(json_blob: Dict) -> Dict | None:
    """Extract the retweeted tweet from a retweet and return it as a separate post record."""
    if not json_blob.get("isRetweet", False):
        return None

    retweet_data = json_blob.get("retweet")
    if not retweet_data or not retweet_data.get("id"):
        return None

    author = retweet_data.get("author", {})
    if not author or "id" not in author:
        return None

    username = author.get("userName", author.get("id"))

    result = {
        "pi_platform_message_id": retweet_data["id"],
        "pi_platform_message_author_id": author.get("id"),
        "pi_platform_message_author_name": username,
        "pi_platform_parent_message_id": None,
        "pi_platform_root_message_id": None,
        "pi_text": retweet_data.get("fullText", retweet_data.get("text", "")),
        "pi_platform_message_url": f"https://x.com/{username}/status/{retweet_data['id']}",
        "platform_message_last_updated_at": datetime.strptime(
            retweet_data["createdAt"], "%a %b %d %H:%M:%S %z %Y"
        ),
        "phoenix_platform_message_id": anonymize(retweet_data["id"]),
        "phoenix_platform_message_author_id": anonymize(author.get("id")),
        "phoenix_platform_parent_message_id": None,
        "phoenix_platform_root_message_id": None,
        "like_count": normalise_to_int(retweet_data.get("likeCount", 0)),
        "share_count": normalise_to_int(retweet_data.get("retweetCount", 0)),
        "comment_count": (
            normalise_to_int(retweet_data.get("quoteCount", 0))
            + normalise_to_int(retweet_data.get("replyCount", 0))
        ),
        "platform": gathers_schemas.Platform.x.value,
        "data_type": gathers_schemas.DataType.posts.value,
        "x_post_retweeted_id": None,
        # Adding the isQuote field from the quoted tweet itself even though this will not be in the
        # tabulated data as currently it is only for comments.
        "x_is_quote": False,
        "x_is_reply": False,
    }

    return add_optional_fields(result)


def extract_quoted_tweet_as_post(json_blob: Dict) -> Dict | None:
    """Extract the quoted tweet from a quote tweet and return it as a separate post record."""
    # Not processing replies
    if json_blob.get("isReply", False):
        return None

    if not json_blob.get("isQuote", False):
        return None

    quote_data = json_blob.get("quote")
    if not quote_data or not quote_data.get("id"):
        return None

    author = quote_data.get("author", {})
    if not author or "id" not in author:
        return None

    username = author.get("userName", author.get("id"))

    result = {
        "pi_platform_message_id": quote_data["id"],
        "pi_platform_message_author_id": author.get("id"),
        "pi_platform_message_author_name": username,
        "pi_platform_parent_message_id": None,
        "pi_platform_root_message_id": None,
        "pi_text": quote_data.get("fullText", quote_data.get("text", "")),
        "pi_platform_message_url": f"https://x.com/{username}/status/{quote_data['id']}",
        "platform_message_last_updated_at": datetime.strptime(
            quote_data["createdAt"], "%a %b %d %H:%M:%S %z %Y"
        ),
        "phoenix_platform_message_id": anonymize(quote_data["id"]),
        "phoenix_platform_message_author_id": anonymize(author.get("id")),
        "phoenix_platform_parent_message_id": None,
        "phoenix_platform_root_message_id": None,
        "like_count": normalise_to_int(quote_data.get("likeCount", 0)),
        "share_count": normalise_to_int(quote_data.get("retweetCount", 0)),
        "comment_count": (
            normalise_to_int(quote_data.get("quoteCount", 0))
            + normalise_to_int(quote_data.get("replyCount", 0))
        ),
        "platform": gathers_schemas.Platform.x.value,
        "data_type": gathers_schemas.DataType.posts.value,
        "x_post_retweeted_id": None,
        # Adding the isQuote field from the quoted tweet itself even though this will not be in the
        # tabulated data as currently it is only for comments.
        "x_is_quote": quote_data.get("isQuote", None),
        "x_is_reply": False,
    }

    return add_optional_fields(result)


def normalise_single_danek_facebook_searches_posts_json(json_blob: Dict) -> Dict | None:
    """Extract fields from a single Danek Facebook search post JSON blob to normalized form."""
    if is_apify_scraping_error(json_blob):
        return None

    if "post_id" not in json_blob and "message" in json_blob:
        # This means there was some error
        return None

    like_count = 0
    # There is a chance that reactions is not in the json_blob
    if "reactions" in json_blob:
        like_count = normalise_to_int(json_blob["reactions"].get("like", 0))

    result = {
        "pi_platform_message_id": json_blob["post_id"],
        "pi_platform_message_author_id": json_blob["author"]["id"],
        "pi_platform_message_author_name": json_blob["author"]["name"],
        "pi_platform_parent_message_id": None,  # Posts don't have parent messages
        "pi_platform_root_message_id": None,  # Posts don't have root messages
        "pi_text": json_blob["message"],
        "pi_platform_message_url": json_blob["url"],
        "platform_message_last_updated_at": datetime.utcfromtimestamp(json_blob["timestamp"]),
        "phoenix_platform_message_id": anonymize(json_blob["post_id"]),
        "phoenix_platform_message_author_id": anonymize(json_blob["author"]["id"]),
        "phoenix_platform_parent_message_id": None,  # Posts don't have parent messages
        "phoenix_platform_root_message_id": None,  # Posts don't have root messages
        # stats
        "like_count": like_count,
        "share_count": normalise_to_int(json_blob.get("reshare_count", 0)),
        "comment_count": normalise_to_int(json_blob.get("comments_count", 0)),
    }
    return add_optional_fields(result)


def normalise_single_danek_instagram_posts_json(json_blob: Dict) -> Dict | None:
    """Extract fields from a single Danek Instagram post JSON blob to normalized form."""
    if is_apify_scraping_error(json_blob):
        return None

    # Basic validation
    if "id" not in json_blob or "user" not in json_blob:
        return None
    if json_blob.get("user", {}).get("id", "") is None:
        return None

    caption = None
    if json_blob.get("caption"):
        caption = json_blob["caption"].get("text")

    result = {
        "pi_platform_message_id": json_blob["pk"],
        "pi_platform_message_author_id": json_blob["user"]["id"],
        "pi_platform_message_author_name": json_blob["user"].get("full_name")
        or json_blob["user"].get("username"),
        "pi_platform_parent_message_id": None,
        "pi_platform_root_message_id": None,
        "pi_text": caption,
        "pi_platform_message_url": f"https://www.instagram.com/p/{json_blob.get('code')}/"
        if json_blob.get("code")
        else None,
        "platform_message_last_updated_at": datetime.utcfromtimestamp(json_blob["taken_at"]),
        # anonymized fields
        "phoenix_platform_message_id": anonymize(json_blob["pk"]),
        "phoenix_platform_message_author_id": anonymize(json_blob["user"]["id"]),
        "phoenix_platform_parent_message_id": None,
        "phoenix_platform_root_message_id": None,
        # stats
        "like_count": normalise_to_int(json_blob.get("like_count", 0))
        + normalise_to_int(json_blob.get("fb_like_count", 0)),
        "share_count": normalise_to_int(json_blob.get("media_repost_count") or 0),
        "comment_count": normalise_to_int(json_blob.get("comment_count", 0)),
    }

    return add_optional_fields(result)


def normalise_single_instagram_comments_json(json_blob: Dict) -> Dict | None:
    """Extract fields from a single Instagram comment JSON blob to normalized form.

    This normaliser can be used for Danek Instagram comments gathers. Assumes that
    `parent_post_id` has already been injected at the node level in the gather batch manager.
    """
    if not json_blob:
        return None

    # Parent post ID injected by gather batch manager
    parent_post_id = json_blob.get("parent_post_id")
    if not parent_post_id:
        return None
    if "pk" not in json_blob:
        return None
    # Parent comment ID if this is a reply; None otherwise
    parent_comment_id = json_blob.get("parent_comment_id")

    # Check that user data is present
    user = json_blob.get("user")
    if not user or "id" not in user:
        return None

    user_id = user.get("id", "").strip()
    if not user_id:
        return None

    username = user.get("username", "").strip()
    if not username:
        username = user_id

    # Build normalized record
    result = {
        "pi_platform_message_id": json_blob["pk"],
        "pi_platform_message_author_id": user_id,
        "pi_platform_message_author_name": username,
        "pi_platform_parent_message_id": parent_comment_id or parent_post_id,
        "pi_platform_root_message_id": parent_post_id,
        "pi_text": json_blob.get("text"),
        "pi_platform_message_url": None,
        "platform_message_last_updated_at": datetime.utcfromtimestamp(
            json_blob.get("created_at", 0)
        ),
        "phoenix_platform_message_id": anonymize(json_blob["pk"]),
        "phoenix_platform_message_author_id": anonymize(user_id),
        "phoenix_platform_parent_message_id": anonymize(parent_comment_id or parent_post_id),
        "phoenix_platform_root_message_id": anonymize(parent_post_id),
        "like_count": normalise_to_int(json_blob.get("comment_like_count", 0)),
        "share_count": 0,
        "comment_count": normalise_to_int(json_blob.get("child_comment_count", 0)),
    }

    return add_optional_fields(result)
