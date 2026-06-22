"""Conftest for tests for the gather pipeline job."""

from datetime import datetime

import pandas as pd
import pytest

from phiphi.api.projects import gathers
from phiphi.pipeline_jobs import generalised_messages
from phiphi.pipeline_jobs.gathers import normalisers
from phiphi.tests.pipeline_jobs.gathers import example_gathers

# Column order constant to match original fixture
EXPECTED_COLUMN_ORDER = [
    "pi_platform_message_id",
    "pi_platform_message_author_id",
    "pi_platform_message_author_name",
    "pi_platform_parent_message_id",
    "pi_platform_root_message_id",
    "pi_text",
    "pi_platform_message_url",
    "platform_message_last_updated_at",
    "phoenix_platform_message_id",
    "phoenix_platform_message_author_id",
    "phoenix_platform_parent_message_id",
    "phoenix_platform_root_message_id",
    "like_count",
    "share_count",
    "comment_count",
    "tiktok_post_plays",
    "x_post_retweeted_id",
    "x_is_quote",
    "x_is_reply",
    "gather_id",
    "gather_batch_id",
    "gathered_at",
    "gather_type",
    "platform",
    "data_type",
    "phoenix_processed_at",
]


def _add_anonymized_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add anonymized phoenix columns based on corresponding pi columns."""
    df_to_anon = df.copy()

    # Create anonymized columns as functions of the pi_ columns
    if "phoenix_platform_message_id" not in df_to_anon.columns:
        df_to_anon["phoenix_platform_message_id"] = df_to_anon["pi_platform_message_id"].apply(
            normalisers.anonymize
        )
    if "phoenix_platform_message_author_id" not in df_to_anon.columns:
        df_to_anon["phoenix_platform_message_author_id"] = df_to_anon[
            "pi_platform_message_author_id"
        ].apply(normalisers.anonymize)

    if "phoenix_platform_parent_message_id" not in df_to_anon.columns:
        df_to_anon["phoenix_platform_parent_message_id"] = df_to_anon[
            "pi_platform_parent_message_id"
        ].apply(lambda x: normalisers.anonymize(x) if x is not None else None)

    if "phoenix_platform_root_message_id" not in df_to_anon.columns:
        df_to_anon["phoenix_platform_root_message_id"] = df_to_anon[
            "pi_platform_root_message_id"
        ].apply(lambda x: normalisers.anonymize(x) if x is not None else None)

    return df_to_anon


def coerce_validate_expected_df(result_df: pd.DataFrame) -> pd.DataFrame:
    """General coercion and validation of expected DataFrame.

    This makes the creation of the expected DataFrame less verbose by handling
    - missing optional columns
    - anonymized columns from the pi_ columns
    - setting gathered_at and phoenix_processed_at to fixed times
    - ordering columns
    - coercing dates
    """
    if "tiktok_post_plays" not in result_df.columns:
        result_df["tiktok_post_plays"] = None
    if "x_post_retweeted_id" not in result_df.columns:
        result_df["x_post_retweeted_id"] = None
    if "x_is_quote" not in result_df.columns:
        result_df["x_is_quote"] = None
    if "x_is_reply" not in result_df.columns:
        result_df["x_is_reply"] = None
    result_df = generalised_messages.coerce_optional_values(result_df)
    result_df = _add_anonymized_columns(result_df)
    result_df["gathered_at"] = pd.to_datetime("2024-04-01T12:00:00.000Z")
    result_df["phoenix_processed_at"] = datetime.fromisoformat("2024-04-02T12:10:59.000Z")
    for column in ["platform_message_last_updated_at", "gathered_at", "phoenix_processed_at"]:
        result_df[column] = result_df[column].astype("datetime64[ms, UTC]")  # type: ignore[call-overload]
    result_df = result_df[EXPECTED_COLUMN_ORDER]
    return generalised_messages.validate(result_df)


@pytest.fixture
def facebook_posts_gather_fixture() -> (
    gathers.apify_facebook_posts.schemas.ApifyFacebookPostsGatherResponse
):
    """Fixture for the Facebook posts gather example."""
    return example_gathers.facebook_posts_gather_example()


@pytest.fixture
def facebook_comments_gather_fixture() -> (
    gathers.apify_facebook_comments.schemas.ApifyFacebookCommentsGatherResponse
):
    """Fixture for the Facebook comments gather example."""
    return example_gathers.facebook_comments_gather_example()


@pytest.fixture
def facebook_search_posts_gather_fixture() -> (
    gathers.apify_facebook_search_posts.schemas.ApifyFacebookSearchPostsGatherResponse
):
    """Fixture for the Facebook search posts gather example."""
    return example_gathers.facebook_search_posts_gather_example()


@pytest.fixture
def tiktok_accounts_posts_gather_fixture() -> (
    gathers.apify_tiktok_accounts_posts.schemas.ApifyTikTokAccountsPostsGatherResponse
):
    """Fixture for the TikTok accounts posts gather example."""
    return example_gathers.tiktok_accounts_posts_gather_example()


@pytest.fixture
def tiktok_hashtags_posts_gather_fixture() -> (
    gathers.apify_tiktok_hashtags_posts.schemas.ApifyTikTokHashtagsPostsGatherResponse
):
    """Fixture for the TikTok hashtags posts gather example."""
    return example_gathers.tiktok_hashtags_posts_gather_example()


@pytest.fixture
def tiktok_searches_posts_gather_fixture() -> (
    gathers.apify_tiktok_searches_posts.schemas.ApifyTikTokSearchesPostsGatherResponse
):
    """Fixture for the TikTok searches posts gather example."""
    return example_gathers.tiktok_searches_posts_gather_example()


@pytest.fixture
def tiktok_comments_gather_fixture() -> (
    gathers.apify_tiktok_comments.schemas.ApifyTikTokCommentsGatherResponse
):
    """Fixture for the TikTok comments gather example."""
    return example_gathers.tiktok_comments_gather_example()


@pytest.fixture
def x_advanced_searches_posts_comments_gather_fixture() -> (
    gathers.apify_x_advanced_searches_posts_comments.schemas.ApifyXAdvancedSearchesPostsCommentsGatherResponse
):
    """Fixture for the X advanced searches posts comments gather example."""
    return example_gathers.x_advanced_searches_posts_comments_gather_example()


@pytest.fixture
def x_simple_searches_posts_comments_gather_fixture() -> (
    gathers.apify_x_simple_searches_posts_comments.schemas.ApifyXSimpleSearchesPostsCommentsGatherResponse
):
    """Fixture for the X simple searches posts comments gather example."""
    return example_gathers.x_simple_searches_posts_comments_gather_example()


@pytest.fixture
def danek_facebook_searches_posts_gather_fixture() -> (
    gathers.danek_facebook_searches_posts.schemas.DanekFacebookSearchesPostsGatherResponse
):
    """Fixture for the Danek Facebook searches posts gather example."""
    return example_gathers.danek_facebook_searches_posts_gather_example()


@pytest.fixture
def danek_instagram_posts_gather_fixture() -> (
    gathers.danek_instagram_posts.schemas.DanekInstagramPostsGatherResponse
):
    """Fixture for the Danek Instagram posts gather example."""
    return example_gathers.danek_instagram_posts_gather_example()


@pytest.fixture
def danek_instagram_comments_gather_fixture() -> (
    gathers.danek_instagram_comments.schemas.DanekInstagramCommentsGatherResponse
):
    """Fixture for the Danek Instagram comments gather example."""
    return example_gathers.danek_instagram_comments_gather_example()


@pytest.fixture
def normalised_facebook_posts_df() -> pd.DataFrame:
    """Return the expected DataFrame based on the processed JSON data."""
    data = {
        "pi_platform_message_id": [
            "843404157832210",
            "837532328419393",
            "818337297005563",
            "824283126394381",
            "823689576453736",
            "823537799802247",
            "817481123757847",
            "823003113189049",
        ],
        "pi_platform_message_author_id": [
            "100064878993116",
            "100064878993116",
            "100064878993116",
            "100064381045972",
            "100064381045972",
            "100064381045972",
            "100064878993116",
            "100064381045972",
        ],
        "pi_platform_message_author_name": [
            "Build Up",
            "Build Up",
            "Build Up",
            "United Nations",
            "United Nations",
            "United Nations",
            "Build Up",
            "United Nations",
        ],
        "pi_platform_parent_message_id": [None, None, None, None, None, None, None, None],
        "pi_platform_root_message_id": [None, None, None, None, None, None, None, None],
        "pi_text": [
            "🗓️✒️ \nhttps://buff.ly/47Bz0N9 👀",
            "... the out! 🚀🎉 \n\n🍿 ",
            "Should digital platforms? 💥",
            "facts.\n\nDefending democracy.\n\nvia",
            "environment. https://www.un.org/en/messengers-peace/jane-goodall",
            "all times.",
            "💡Be initiatives",
            "round the world.",
        ],
        "pi_platform_message_url": [
            "https://www.facebook.com/howtobuildup/posts/pfbid0wY5Xr9MbMh6Vtfd1fjhgCBCvmtTMpYpiQBENdy3kZen1tqyHc7KRR1AXqMVbtRoXl",
            "https://www.facebook.com/howtobuildup/posts/pfbid0Pgnmi21mzGgyWgckpc6Rrz2JfzuDM8SAnyXFPzUR7bkef6fbcAfiKgzEkwftJR5Wl",
            "https://www.facebook.com/howtobuildup/posts/pfbid02ubha39CEo7VofcosVvZ1oKXnyVxNrJK9L2DtPkZkeJKS76qzmaF1etSxtVEG2fiWl",
            "https://www.facebook.com/unitednations/posts/pfbid0eCoKhMP3ssi9fxqUT22C422scmU13UfrgWcquVwN5S3g35K5NdA42cbXWEipQyjdl",
            "https://www.facebook.com/unitednations/posts/pfbid045as8QKV2uLVYe2NumDPs7a68Hr4P5cjmoyMRo2e4dj4p3rp2gWNNj948Uu7BVcxl",
            "https://www.facebook.com/unitednations/posts/pfbid02qcW6e6RMSDQ5DT1ZB2o19N9zMBRdETnskgEyEGoLdPCMdxd7jr8ip7KK1JA8cgW5l",
            "https://www.facebook.com/howtobuildup/posts/pfbid0SJ9vqgSJsF7x1RFQjr3yp7rgYNumzJmJW7A5Xa8wEDTWuX21b2HkA4HyCH8fiaLPl",
            "https://www.facebook.com/unitednations/posts/pfbid0LmBjLodaYjFhvntY3rX4xB2cyrcUeXHuasXJNFgimkNX7NE76CjSEYCwwveF9v5ml",
        ],
        "platform_message_last_updated_at": [
            datetime.fromisoformat("2024-04-03T06:00:25.000Z"),
            datetime.fromisoformat("2024-03-25T07:00:17.000Z"),
            datetime.fromisoformat("2024-02-22T16:00:01.000Z"),
            datetime.fromisoformat("2024-04-03T18:02:22.000Z"),
            datetime.fromisoformat("2024-04-03T08:02:00.000Z"),
            datetime.fromisoformat("2024-04-02T18:04:00.000Z"),
            datetime.fromisoformat("2024-02-21T08:00:10.000Z"),
            datetime.fromisoformat("2024-04-02T08:07:30.000Z"),
        ],
        "like_count": [4000000, 3, 2, 477, 1259, 956, 3, 2327],
        "share_count": [1000000000, 3, 0, 171, 261, 347, 1, 1054],
        "comment_count": [0, 0, 0, 203, 229000, 388, 0, 214],
    }

    df = pd.DataFrame(data)  # noqa: PD901
    df["gather_id"] = 1
    df["gather_batch_id"] = 3
    df["gather_type"] = gathers.schemas.ChildTypeName.apify_facebook_posts.value
    df["platform"] = gathers.schemas.Platform.facebook
    df["data_type"] = gathers.schemas.DataType.posts
    return coerce_validate_expected_df(df)


@pytest.fixture
def normalised_facebook_search_posts_df() -> pd.DataFrame:
    """Return the expected DataFrame based on the processed JSON data."""
    data = {
        "pi_platform_message_id": [
            "facebook_search_posts-postId1",
            "facebook_search_posts-postId2",
            "facebook_search_posts-postId3",
            "facebook_search_posts-postId4",
        ],
        "pi_platform_message_author_id": [
            "facebook_search_posts-authorID1",
            "facebook_search_posts-authorID2",
            "facebook_search_posts-authorID3",
            "facebook_search_posts-authorID4",
        ],
        "pi_platform_message_author_name": [
            "facebook_search_posts-authorName1",
            "facebook_search_posts-authorName2",
            "facebook_search_posts-authorName3",
            "facebook_search_posts-authorName4",
        ],
        "pi_platform_parent_message_id": [None] * 4,
        "pi_platform_root_message_id": [None] * 4,
        "pi_text": [
            "ONE MORE HELLO OR ONE LAST GOODBYE! \\ud83d",
            "One more hello or one last goodbye? \\n\\nWitness their new world.",
            "test",
            "One more hello or one last goodbye? \\u2708\\ufe0f",
        ],
        "pi_platform_message_url": [
            "https://www.facebook.com/authorId1/posts/urlId1",
            "https://www.facebook.com/authorId2/videos/urlId2",
            "https://www.facebook.com/authorId3/videos/urlId3",
            "https://www.facebook.com/authorId4/videos/urlId4",
        ],
        "platform_message_last_updated_at": [
            datetime.utcfromtimestamp(1728388135),
            datetime.utcfromtimestamp(1728387357),
            datetime.utcfromtimestamp(1728385343),
            datetime.utcfromtimestamp(1728387354),
        ],
        "like_count": [91000000, 125, 3, 0],
        "share_count": [0] * 4,
        "comment_count": [15000, 43, 0, 3],
    }

    df = pd.DataFrame(data)  # noqa: PD901
    df["gather_id"] = 7
    df["gather_batch_id"] = 3
    df["gather_type"] = gathers.schemas.ChildTypeName.apify_facebook_search_posts.value
    df["platform"] = gathers.schemas.Platform.facebook
    df["data_type"] = gathers.schemas.DataType.posts
    df["platform_message_last_updated_at"] = df["platform_message_last_updated_at"].dt.tz_localize(
        "UTC"
    )

    return coerce_validate_expected_df(df)


@pytest.fixture
def normalised_facebook_comments_df() -> pd.DataFrame:
    """Return the expected DataFrame based on the processed JSON data."""
    data = {
        "pi_platform_message_id": [
            "Y29tbWVudDo4MjM2ODk1NzY0NTM3MzZfOTYxNjQ3MDc4ODA5NzM1",
            "Y29tbWVudDo4MjM2ODk1NzY0NTM3MzZfNzcyNTQ5MjA4MTc0NjM4",
            "Y29tbWVudDo4MjM2ODk1NzY0NTM3MzZfOTQyNjY5MDc0MTkwNTIz",
            "Y29tbWVudDo4MjM2ODk1NzY0NTM3MzZfMTUyMDM5OTc0ODU5MzY2NA==",
            "Y29tbWVudDo4MjMwMDMxMTMxODkwNDlfNzI1MjA5MDE2NDMyMjAz",
            "Y29tbWVudDo4MjMwMDMxMTMxODkwNDlfNzI4NTI5NDQ2ODE4NTgxOA==",
            "Y29tbWVudDo4MjMwMDMxMTMxODkwNDlfMTM1Njc3Njg4NDk5NzU1Mg==",
            "Y29tbWVudDo4MjMwMDMxMTMxODkwNDlfMTEzNzU1NDU2NDE2MjcwMQ==",
            "Y29tbWVudDo3NjM3MTY1OTE5NjYwMzMyXzQyNjU5NzcyOTk5MDI2OA==",
        ],
        "pi_platform_message_author_id": [
            "100064878993116",
            "100024915288912",
            "pfbid0M9N6BtGwe2g76dEPzMAsmRa4xUowvx8ohdMHbqHgCfssWyap6Gyr6RueezmvZeXml",
            "pfbid02n7VKGoXEYpLj5vMDb8QCk2ZY7wbqqudAz25ftbqGwTm7D5vKPWw8qNtHwy5mqBiql",
            "100087182205819",
            "pfbid0aZ3q95k4ZMWH6T3XSSJybx5kLrSCXRW9ZFRoxyQT7ji1xsM9UL5LECHqdyKoEUzql",
            "100063654872822",
            "pfbid0txFVuZ1ib4vwyB1ieojzyWZ8DoWtG6sR2W8dHP6EHZ5Gmw2TBz4bVk1fiAxdbeKYl",
            "pfbid02wia9a2GDCRqQH2aSty35ZBwNMHZpys2UajNSYaW1sKLxNxw22Ebc1Vk64KusqWnxl",
        ],
        "pi_platform_message_author_name": [
            "Build Up",
            "Sally Yuan",
            "Jamil Mohammad",
            "Judy Haila",
            "एक युद्ध पाखंडवाद व अंधविश्वास के खिलाफ",
            "Ashraf Rahman",
            "Rex Omolleh Nairobi West Ward MCA.",
            "Cynthia Keels",
            "Bah Rahman Bouba",
        ],
        "pi_platform_parent_message_id": [
            "823689576453736",
            "823689576453736",
            "823689576453736",
            "823689576453736",
            "823003113189049",
            "823003113189049",
            "823003113189049",
            "823003113189049",
            "Y29tbWVudDo3NjM3MTY1OTE5NjYwMzMyXzc5MTgyMjgxMTQ4OTUwNDY=",
        ],
        "pi_platform_root_message_id": [
            "823689576453736",
            "823689576453736",
            "823689576453736",
            "823689576453736",
            "823003113189049",
            "823003113189049",
            "823003113189049",
            "823003113189049",
            "7637165919660332",
        ],
        "pi_text": [
            "Birthday wishes Dr.Jane Goodall. world.",
            "Happy birthday",
            "Best wishes of Happy Birthday",
            "Happy Birthday. Thank you for doing what you do to make our planet a better place.",
            "The main goal of all of us should be to build a.",
            "Thanks a lot to all of you do for huminity👍❤️",
            "Awesome 👏 \nHappy autism day",
            "and thank you lord and thank you God Amen",
            # No "text" key in blob is for comment that are images. We include them but with empty
            # text
            "",
        ],
        "pi_platform_message_url": [
            "https://www.facebook.com/unitednations/posts/pfbid045as8QKV2uLVYe2NumDPs7a68Hr4P5cjmoyMRo2e4dj4p3rp2gWNNj948Uu7BVcxl?comment_id=961647078809735",
            "https://www.facebook.com/unitednations/posts/pfbid045as8QKV2uLVYe2NumDPs7a68Hr4P5cjmoyMRo2e4dj4p3rp2gWNNj948Uu7BVcxl?comment_id=772549208174638",
            "https://www.facebook.com/unitednations/posts/pfbid045as8QKV2uLVYe2NumDPs7a68Hr4P5cjmoyMRo2e4dj4p3rp2gWNNj948Uu7BVcxl?comment_id=942669074190523",
            "https://www.facebook.com/unitednations/posts/pfbid045as8QKV2uLVYe2NumDPs7a68Hr4P5cjmoyMRo2e4dj4p3rp2gWNNj948Uu7BVcxl?comment_id=1520399748593664",
            "https://www.facebook.com/unitednations/posts/pfbid0LmBjLodaYjFhvntY3rX4xB2cyrcUeXHuasXJNFgimkNX7NE76CjSEYCwwveF9v5ml?comment_id=725209016432203",
            "https://www.facebook.com/unitednations/posts/pfbid0LmBjLodaYjFhvntY3rX4xB2cyrcUeXHuasXJNFgimkNX7NE76CjSEYCwwveF9v5ml?comment_id=7285294468185818",
            "https://www.facebook.com/unitednations/posts/pfbid0LmBjLodaYjFhvntY3rX4xB2cyrcUeXHuasXJNFgimkNX7NE76CjSEYCwwveF9v5ml?comment_id=1356776884997552",
            "https://www.facebook.com/unitednations/posts/pfbid0LmBjLodaYjFhvntY3rX4xB2cyrcUeXHuasXJNFgimkNX7NE76CjSEYCwwveF9v5ml?comment_id=1137554564162701",
            "https://www.facebook.com/malick.konate.56/posts/7637165919660332?comment_id=426597729990268",
        ],
        "platform_message_last_updated_at": [
            datetime.fromisoformat("2024-04-03T08:58:38.000Z"),
            datetime.fromisoformat("2024-04-03T10:59:05.000Z"),
            datetime.fromisoformat("2024-04-03T09:03:29.000Z"),
            datetime.fromisoformat("2024-04-03T17:47:58.000Z"),
            datetime.fromisoformat("2024-04-03T04:56:01.000Z"),
            datetime.fromisoformat("2024-04-02T15:21:12.000Z"),
            datetime.fromisoformat("2024-04-02T09:04:43.000Z"),
            datetime.fromisoformat("2024-04-02T10:59:46.000Z"),
            datetime.fromisoformat("2024-04-22T19:12:51.000Z"),
        ],
        "like_count": [4000, 2, 2, 1, 1, 1, 0, 2, 0],
        "share_count": [0, 0, 0, 0, 0, 0, 0, 0, 0],
        "comment_count": [1, 3000, 2, 0, 0, 2, 0, 5, 0],
    }

    df = pd.DataFrame(data)  # noqa: PD901
    df["gather_id"] = 2
    df["gather_batch_id"] = 3
    df["gather_type"] = gathers.schemas.ChildTypeName.apify_facebook_comments.value
    df["platform"] = gathers.schemas.Platform.facebook
    df["data_type"] = gathers.schemas.DataType.comments
    return coerce_validate_expected_df(df)


@pytest.fixture
def normalised_tiktok_accounts_posts_df() -> pd.DataFrame:
    """Return the expected DataFrame based on the processed JSON data."""
    data = {
        "pi_platform_message_id": [
            "tiktok-accounts-id1",
            "tiktok-accounts-id2",
            "tiktok-accounts-id3",
        ],
        "pi_platform_message_author_id": [
            "tiktok-accounts-authorMetaId1",
            "tiktok-accounts-authorMetaId2",
            "tiktok-accounts-authorMetaId3",
        ],
        "pi_platform_message_author_name": ["bbcnews", "bbcnews", "bbcnews"],
        "pi_platform_parent_message_id": [None, None, None],
        "pi_platform_root_message_id": [None, None, None],
        "pi_text": [
            "US President Joe Biden mistakenly referred ... \\u201cPresident Putin\\u201d ...",
            "... the son of Asia\\'s richest man, ... \\u00a0#India #Mumbai #IndianWedding ...",
            "Do you think a deal can be made? #JuniorDoctors #JuniorDoctorStrikes #WesStreeting",
        ],
        "pi_platform_message_url": [
            "https://www.tiktok.com/@bbcnews/video/webVideoUrl1",
            "https://www.tiktok.com/@bbcnews/video/webVideoUrl2",
            "https://www.tiktok.com/@bbcnews/video/webVideoUrl3",
        ],
        "platform_message_last_updated_at": [1720741311000, 1720731600000, 1720729800000],
        "like_count": [226000, 6804, 1314],
        "share_count": [6000000, 244, 11],
        "comment_count": [174000, 232, 65],
        "tiktok_post_plays": [1200000, 154400, 46100],
    }
    normalised_tiktok_df = pd.DataFrame(data)
    normalised_tiktok_df["gather_id"] = 3
    normalised_tiktok_df["gather_batch_id"] = 3
    normalised_tiktok_df["gather_type"] = (
        gathers.schemas.ChildTypeName.apify_tiktok_accounts_posts.value
    )
    normalised_tiktok_df["platform"] = gathers.schemas.Platform.tiktok
    normalised_tiktok_df["data_type"] = gathers.schemas.DataType.posts
    return coerce_validate_expected_df(normalised_tiktok_df)


@pytest.fixture
def normalised_tiktok_searches_posts_df() -> pd.DataFrame:
    """Return the expected DataFrame based on the processed JSON data."""
    data = {
        "pi_platform_message_id": [
            "tiktok-searches-id1",
            "tiktok-searches-id2",
            "tiktok-searches-id3",
            "tiktok-searches-id4",
            "tiktok-searches-id5",
            "tiktok-searches-id6",
        ],
        "pi_platform_message_author_id": [
            "tiktok-searches-authorMetaId1",
            "tiktok-searches-authorMetaId2",
            "tiktok-searches-authorMetaId3",
            "tiktok-searches-authorMetaId4",
            "tiktok-searches-authorMetaId5",
            "tiktok-searches-authorMetaId6",
        ],
        "pi_platform_message_author_name": [
            "tiktok-searches-authorMetaName1",
            "tiktok-searches-authorMetaName2",
            "tiktok-searches-authorMetaName3",
            "tiktok-searches-authorMetaName4",
            "tiktok-searches-authorMetaName5",
            "tiktok-searches-authorMetaName6",
        ],
        "pi_platform_parent_message_id": [None] * 6,
        "pi_platform_root_message_id": [None] * 6,
        "pi_text": [
            "Finding peace often requires letting go of people",
            "You find peace in the countryside #countrysidelife",
            "for my birthday I want PEACE and NO human interaction",
            "Hello World #programming #coding #python #codingmemes ",
            "#helloworld #painisanillusion #fyp I am a trained martial arts practitioner",
            "text6",
        ],
        "pi_platform_message_url": [
            "https://www.tiktok.com/@tiktok-searches-authorMetaProfileUrl1/video/id1",
            "https://www.tiktok.com/@tiktok-searches-authorMetaProfileUrl2/video/id2",
            "https://www.tiktok.com/@tiktok-searches-authorMetaProfileUrl3/video/id3",
            "https://www.tiktok.com/@tiktok-searches-authorMetaProfileUrl4/video/id4",
            "https://www.tiktok.com/@tiktok-searches-authorMetaProfileUrl5/video/id5",
            "https://www.tiktok.com/@tiktok-searches-authorMetaProfileUrl6/video/id6",
        ],
        "platform_message_last_updated_at": [
            1676503649000,
            1715610890000,
            1721064158000,
            1725019495000,
            1723029970000,
            1725793230000,
        ],
        "like_count": [54100, 469900, 105500, 491200, 0, 0],
        "share_count": [11800, 15200, 3500, 77300, 0, 0],
        "comment_count": [304, 2197, 900, 4112, 2496, 0],
        "tiktok_post_plays": [150000, 2500000, 2400000, 3900000, 3800000, 1500000],
    }
    normalised_tiktok_df = pd.DataFrame(data)
    normalised_tiktok_df["gather_id"] = 6
    normalised_tiktok_df["gather_batch_id"] = 3
    normalised_tiktok_df["gather_type"] = (
        gathers.schemas.ChildTypeName.apify_tiktok_searches_posts.value
    )
    normalised_tiktok_df["platform"] = gathers.schemas.Platform.tiktok
    normalised_tiktok_df["data_type"] = gathers.schemas.DataType.posts
    return coerce_validate_expected_df(normalised_tiktok_df)


@pytest.fixture
def normalised_tiktok_hashtags_posts_df() -> pd.DataFrame:
    """Return the expected DataFrame based on the processed JSON data."""
    data = {
        "pi_platform_message_id": [
            "tiktok-hashtags-id1",
            "tiktok-hashtags-id2",
            "tiktok-hashtags-id3",
            "tiktok-hashtags-id4",
            "tiktok-hashtags-id5",
            "tiktok-hashtags-id6",
        ],
        "pi_platform_message_author_id": [
            "tiktok-hashtags-authorMetaId1",
            "tiktok-hashtags-authorMetaId2",
            "tiktok-hashtags-authorMetaId3",
            "tiktok-hashtags-authorMetaId4",
            "tiktok-hashtags-authorMetaId5",
            "tiktok-hashtags-authorMetaId6",
        ],
        "pi_platform_message_author_name": [
            "bbcnews",
            "bbcnews",
            "bbcnews",
            "authorMetaName4",
            "unitednations",
            "cbsnews",
        ],
        "pi_platform_parent_message_id": [None] * 6,
        "pi_platform_root_message_id": [None] * 6,
        "pi_text": [
            "There's still time to see it! #BBCNews",
            "At the Democratic National Convention",
            "A major crackdown on smokers and vapers #BBCNews",
            "The #unitednations #knowledge",
            "The war in #Sudan has displaced 10 million people. #UnitedNations",
            "President Biden tells the U.N. #news #biden #unitednations ",
        ],
        "pi_platform_message_url": [
            "https://www.tiktok.com/@bbcnews/video/webVideoUrl1",
            "https://www.tiktok.com/@bbcnews/video/webVideoUrl2",
            "https://www.tiktok.com/@bbcnews/video/webVideoUrl3",
            "https://www.tiktok.com/@authorMetaName4/video/webVideoUrl4",
            "https://www.tiktok.com/@unitednations/video/webVideoUrl5",
            "https://www.tiktok.com/@cbsnews/video/webVideoUrl6",
        ],
        "platform_message_last_updated_at": [
            1724086800000,
            1724219490000,
            1721216700000,
            1716304501000,
            1721748028000,
            1663784721000,
        ],
        "like_count": [137800, 4955, 211900, 6845, 729, 674900],
        "share_count": [16200, 152, 24000, 542, 46, 12600],
        "comment_count": [1167, 181, 7705, 0, 485, 18100],
        "tiktok_post_plays": [1700000, 67800, 5300000, 276300, 24500, 8800000],
    }
    normalised_tiktok_df = pd.DataFrame(data)
    normalised_tiktok_df["gather_id"] = 4
    normalised_tiktok_df["gather_batch_id"] = 3
    normalised_tiktok_df["gather_type"] = (
        gathers.schemas.ChildTypeName.apify_tiktok_hashtags_posts.value
    )
    normalised_tiktok_df["platform"] = gathers.schemas.Platform.tiktok
    normalised_tiktok_df["data_type"] = gathers.schemas.DataType.posts
    return coerce_validate_expected_df(normalised_tiktok_df)


@pytest.fixture
def normalised_tiktok_comments_df() -> pd.DataFrame:
    """Return the expected DataFrame based on the processed JSON data."""
    data = {
        "pi_platform_message_id": [
            "anonymizedID1",
            "anonymizedID2",
            "anonymizedID3",
            "anonymizedID4",
            "anonymizedID5",
            "anonymizedID6",
        ],
        "pi_platform_message_author_id": [
            "anonymizedUserID1",
            "anonymizedUserID2",
            "anonymizedUserID3",
            "anonymizedUserID4",
            "anonymizedUserID5",
            "anonymizedUserID6",
        ],
        "pi_platform_message_author_name": [
            "anonymizedUsername1",
            "anonymizedUsername2",
            "anonymizedUsername3",
            "anonymizedUsername4",
            "anonymizedUserID5",  # Uses user_id when username is missing
            "anonymizedUserID6",  # Uses user_id when username is empty
        ],
        "pi_platform_parent_message_id": [
            "anonymizedAwemeID1",
            "anonymizedAwemeID2",
            "anonymizedAwemeID3",
            "anonymizedParentID4",
            "anonymizedAwemeID5",
            "anonymizedAwemeID6",
        ],
        "pi_platform_root_message_id": [
            "anonymizedAwemeID1",
            "anonymizedAwemeID2",
            "anonymizedAwemeID3",
            "anonymizedAwemeID4",
            "anonymizedAwemeID5",
            "anonymizedAwemeID6",
        ],
        "pi_text": [
            (
                "please help save [country's] water bodies. "
                "they are being destroyed by illegal mining activities"
            ),
            "",
            "[International organization], please take care of the foreigners in [country]",
            "womp womp",
            "This user has no username field",
            "This user has empty username",
        ],
        "pi_platform_message_url": [None] * 6,
        "platform_message_last_updated_at": [
            datetime.fromisoformat("2024-09-09T18:40:45.000Z"),
            datetime.fromisoformat("2024-09-10T06:29:28.000Z"),
            datetime.fromisoformat("2024-09-09T23:46:51.000Z"),
            datetime.fromisoformat("2024-06-02T07:09:12.000Z"),
            datetime.fromisoformat("2024-10-23T01:12:13.000Z"),
            datetime.fromisoformat("2024-10-23T02:15:30.000Z"),
        ],
        "like_count": [1000, 0, 0, 3, 0, 1],
        "share_count": [0, 0, 0, 0, 0, 0],
        "comment_count": [1, 1000000, 0, 0, 0, 0],
    }
    normalised_tiktok_df = pd.DataFrame(data)
    normalised_tiktok_df["gather_id"] = 5
    normalised_tiktok_df["gather_batch_id"] = 3
    normalised_tiktok_df["gather_type"] = gathers.schemas.ChildTypeName.apify_tiktok_comments.value
    normalised_tiktok_df["platform"] = gathers.schemas.Platform.tiktok
    normalised_tiktok_df["data_type"] = gathers.schemas.DataType.comments
    return coerce_validate_expected_df(normalised_tiktok_df)


@pytest.fixture
def normalised_x_advanced_searches_posts_comments_df() -> pd.DataFrame:
    """Return the expected DataFrame based on the processed X JSON data."""
    data = {
        "pi_platform_message_id": [
            "tweet_id_1",  # Regular post
            "tweet_id_2",  # Reply + Quote (treated as reply)
            "tweet_id_3",  # Regular post
            "tweet_id_4",  # Retweet post
            "retweeted_tweet_id_1",  # Extracted original from retweet
            "tweet_id_5",  # Regular reply
            "tweet_id_6",  # Quote tweet (as comment)
            "quote_tweet_id_6",  # Extracted quoted tweet
            # tweet_id_7 and tweet_id_8 are skipped (null author and author without id)
            "tweet_id_9_no_username",  # Regular post with author id but no username
            "tweet_id_10_reply_no_username",  # Reply with author id but no username
            "tweet_id_11_quote_no_username",  # Quote tweet with author id but no username
            "quoted_tweet_id_11",  # Extracted quoted tweet from tweet_id_11
        ],
        "pi_platform_message_author_id": [
            "author_id_1",
            "author_id_1",
            "author_id_1",
            "author_id_4",
            "author_id_5",
            "author_id_5",
            "author_id_6",
            "quote_author_id_6",
            "author_id_9",  # Uses id as username
            "author_id_10",  # Uses id as username
            "author_id_11",  # Uses id as username
            "quoted_author_id_11",
        ],
        "pi_platform_message_author_name": [
            "user_name_1",
            "user_name_1",
            "user_name_1",
            "tweet_author_4",
            "author_user_name_5",
            "user_name_5",
            "user_name_6",
            "quote_user_name_6",
            "author_id_9",  # Falls back to author id when userName is missing
            "author_id_10",  # Falls back to author id when userName is missing
            "author_id_11",  # Falls back to author id when userName is missing
            "quoted_user_11",
        ],
        "pi_platform_parent_message_id": [
            # Regular post has no parent
            None,
            # Reply + Quote tweet has inReplyToId as parent
            "in_reply_to_id_1",
            # Regular post has no parent
            None,
            # Retweet post has no parent
            None,
            # Extracted original from retweet has no parent
            None,
            # Regular reply has parent as the original tweet
            "in_reply_to_tweet_id_1",
            # Quote tweet has quote id as parent
            "quote_tweet_id_6",
            # Expected quote tweet has no parent
            None,
            # Regular post with no username - no parent
            None,
            # Reply with no username - has parent
            "parent_tweet_id_10",
            # Quote tweet with no username - has quoted tweet as parent
            "quoted_tweet_id_11",
            # Extracted quoted tweet - no parent
            None,
        ],
        "pi_platform_root_message_id": [
            # Regular post has no root
            None,
            # Reply + Quote tweet has conversation id as root
            "con_tweet_id_3",
            # Regular post has no root
            None,
            # Retweet post has no root
            None,
            # Extracted original from retweet has no root
            None,
            # Regular reply has conversationID as roote
            "con_tweet_id_1",
            # Conversation id for quote tweet
            "con_tweet_id_6",
            # Non conversation id for extracted quoted tweet
            None,
            # Regular post with no username - no root
            None,
            # Reply with no username - has conversation id as root
            "conv_id_10",
            # Quote tweet with no username - has conversation id as root
            "conv_id_11",
            # Extracted quoted tweet - no root
            None,
        ],
        "pi_text": [
            "Full text tweet 1",
            "Full text tweet 2",
            "Full text tweet 3",
            "Full text tweet 4",
            "Text tweet 5",
            "@user_name_1 This is a reply tweet",
            "Full text tweet 6",
            "Full Quote text tweet 6",
            "Regular post with author id but no username - should use id as username",
            "@someone Reply with author id but no username - should use id as username",
            "Quote tweet with author id but no username - should use id as username",
            "Original quoted tweet 11 full text",
        ],
        "pi_platform_message_url": [
            "https://x.com/user_name_1/status/tweet_id_1",
            "https://x.com/user_name_1/status/tweet_id_2",
            "https://x.com/user_name_1/status/tweet_id_3",
            "https://x.com/tweet_author_4/status/tweet_id_4",
            "https://x.com/author_user_name_5/status/retweeted_tweet_id_1",
            "https://x.com/user_name_5/status/tweet_id_5",
            "https://x.com/user_name_6/status/tweet_id_6",
            "https://x.com/quote_user_name_6/status/quote_tweet_id_6",
            "https://x.com/author_id_9/status/tweet_id_9_no_username",
            "https://x.com/author_id_10/status/tweet_id_10_reply_no_username",
            "https://x.com/author_id_11/status/tweet_id_11_quote_no_username",
            "https://x.com/quoted_user_11/status/quoted_tweet_id_11",
        ],
        "platform_message_last_updated_at": [
            datetime.strptime("Fri Jan 31 16:47:08 +0000 2025", "%a %b %d %H:%M:%S %z %Y"),
            datetime.strptime("Thu Jan 30 23:05:43 +0000 2025", "%a %b %d %H:%M:%S %z %Y"),
            datetime.strptime("Thu Jan 30 22:32:31 +0000 2025", "%a %b %d %H:%M:%S %z %Y"),
            datetime.strptime("Thu Sep 11 09:37:57 +0000 2025", "%a %b %d %H:%M:%S %z %Y"),
            datetime.strptime("Thu Sep 11 08:59:37 +0000 2025", "%a %b %d %H:%M:%S %z %Y"),
            datetime.strptime("Fri Jan 31 18:30:12 +0000 2025", "%a %b %d %H:%M:%S %z %Y"),
            datetime.strptime("Sat Feb 01 09:45:18 +0000 2025", "%a %b %d %H:%M:%S %z %Y"),
            datetime.strptime("Thu Jan 30 22:32:31 +0000 2025", "%a %b %d %H:%M:%S %z %Y"),
            datetime.strptime("Mon Feb 03 12:00:00 +0000 2025", "%a %b %d %H:%M:%S %z %Y"),
            datetime.strptime("Mon Feb 03 13:00:00 +0000 2025", "%a %b %d %H:%M:%S %z %Y"),
            datetime.strptime("Mon Feb 03 14:00:00 +0000 2025", "%a %b %d %H:%M:%S %z %Y"),
            datetime.strptime("Sun Feb 02 10:00:00 +0000 2025", "%a %b %d %H:%M:%S %z %Y"),
        ],
        "like_count": [1290, 23, 2104, 0, 0, 15, 42, 2104, 10, 3, 8, 500],
        "share_count": [291, 4, 398, 1, 1, 2, 8, 398, 5, 1, 2, 100],
        "comment_count": [236, 1, 247, 0, 0, 1, 5, 247, 3, 0, 1, 75],
        "tiktok_post_plays": [None] * 12,
        "x_post_retweeted_id": [
            None,  # Regular post
            None,  # Reply
            None,  # Regular post
            "retweeted_tweet_id_1",
            None,  # Extracted original (not a retweet)
            None,  # Reply
            None,  # Quote tweet
            None,  # Extracted quoted tweet
            None,  # Regular post with no username
            None,  # Reply with no username
            None,  # Quote tweet with no username
            None,  # Extracted quoted tweet
        ],
        "data_type": [
            "posts",  # tweet_id_1: Regular post
            "comments",  # tweet_id_2: Reply (takes precedence over quote)
            "posts",  # tweet_id_3: Regular post
            "posts",  # tweet_id_4: Retweet (becomes post)
            "posts",  # retweeted_tweet_id_1: Extracted original (post)
            "comments",  # tweet_id_5: Reply
            "comments",  # tweet_id_6: Quote tweet (comment)
            "posts",  # quote_tweet_id_6: Extracted quoted tweet (post)
            "posts",  # tweet_id_9: Regular post with no username
            "comments",  # tweet_id_10: Reply with no username
            "comments",  # tweet_id_11: Quote tweet with no username
            "posts",  # quoted_tweet_id_11: Extracted quoted tweet
        ],
        "x_is_quote": [
            False,
            True,
            False,
            False,
            False,
            False,
            True,
            False,
            False,  # Regular post
            False,  # Reply
            True,  # Quote tweet
            False,  # Extracted quoted tweet
        ],
        "x_is_reply": [
            False,
            True,
            False,
            False,
            False,
            True,
            False,
            False,
            False,  # Regular post
            True,  # Reply
            False,  # Quote tweet
            False,  # Extracted quoted tweet
        ],
    }

    result_df = pd.DataFrame(data)
    result_df["gather_id"] = 1
    result_df["gather_batch_id"] = 3
    result_df["gather_type"] = (
        gathers.schemas.ChildTypeName.apify_x_advanced_searches_posts_comments.value
    )
    result_df["platform"] = gathers.schemas.Platform.x
    return coerce_validate_expected_df(result_df)


@pytest.fixture
def normalised_x_simple_searches_posts_comments_df(
    normalised_x_advanced_searches_posts_comments_df: pd.DataFrame,
) -> pd.DataFrame:
    """Return the expected DataFrame based on the processed X JSON data.

    Currently the simple searches use the same data as advanced searches.
    """
    result_df = normalised_x_advanced_searches_posts_comments_df.copy()
    result_df["gather_type"] = (
        gathers.schemas.ChildTypeName.apify_x_simple_searches_posts_comments.value
    )
    return result_df


@pytest.fixture
def normalised_danek_facebook_searches_posts_df() -> pd.DataFrame:
    """Return the expected DataFrame based on the processed JSON data."""
    data = {
        "pi_platform_message_id": [
            "danek_facebook_search_posts-postId1",
            "danek_facebook_search_posts-postId2",
            "danek_facebook_search_posts-postId3",
            "danek_facebook_search_posts-postId4",
            "danek_facebook_search_posts-postId5",
            "danek_facebook_search_posts-postId6",
        ],
        "pi_platform_message_author_id": [
            "danek_facebook_search_posts-authorId1",
            "danek_facebook_search_posts-authorId2",
            "danek_facebook_search_posts-authorId3",
            "danek_facebook_search_posts-authorId4",
            "danek_facebook_search_posts-authorId5",
            "danek_facebook_search_posts-authorId6",
        ],
        "pi_platform_message_author_name": [
            "danek_facebook_search_posts-authorName1",
            "danek_facebook_search_posts-authorName2",
            "danek_facebook_search_posts-authorName3",
            "danek_facebook_search_posts-authorName4",
            "danek_facebook_search_posts-authorName5",
            "danek_facebook_search_posts-authorName6",
        ],
        "pi_platform_parent_message_id": [None] * 6,
        "pi_platform_root_message_id": [None] * 6,
        "pi_text": [
            "Innovation is our middle name!",
            "Sannad Cusub oo Farxad leh oo ka yimid ",
            # Not that the Unicode changes
            "Follow \U0001f449\U0001f449 Tech Innovation for more",
            "test 4",
            "test 5",
            "test 6",
        ],
        "pi_platform_message_url": [
            "https://www.facebook.com/authorId1/posts/urlId1",
            "https://www.facebook.com/authorId2/posts/urlId2",
            "https://www.facebook.com/authorId3/posts/urlId3",
            "https://www.facebook.com/authorId4/posts/urlId4",
            "https://www.facebook.com/authorId5/posts/urlId5",
            "https://www.facebook.com/authorId6/posts/urlId6",
        ],
        "platform_message_last_updated_at": [
            datetime.utcfromtimestamp(1704196727),
            datetime.utcfromtimestamp(1704091324),
            datetime.utcfromtimestamp(1704198271),
            datetime.utcfromtimestamp(1704196827),
            datetime.utcfromtimestamp(1704130325),
            datetime.utcfromtimestamp(1704100378),
        ],
        "like_count": [0, 10, 24000, 3, 15, 2],
        "share_count": [0, 10, 7, 0, 3, 0],
        "comment_count": [0, 1, 2, 0, 0, 0],
    }

    df = pd.DataFrame(data)  # noqa: PD901
    df["gather_id"] = 8
    df["gather_batch_id"] = 3
    df["gather_type"] = gathers.schemas.ChildTypeName.danek_facebook_searches_posts.value
    df["platform"] = gathers.schemas.Platform.facebook
    df["data_type"] = gathers.schemas.DataType.posts
    df["platform_message_last_updated_at"] = df["platform_message_last_updated_at"].dt.tz_localize(
        "UTC"
    )
    return coerce_validate_expected_df(df)


@pytest.fixture
def normalised_danek_instagram_posts_df() -> pd.DataFrame:
    """Return the expected DataFrame based on the processed JSON data."""
    data = {
        "pi_platform_message_id": [
            "post_0001",
            "post_0008",
            "post_0049",
        ],
        "pi_platform_message_author_id": [
            "pk_user_0006",
            "pk_user_0006",
            "pk_user_0054",
        ],
        "pi_platform_message_author_name": [
            "full_name_user_0006",
            "full_name_user_0006",
            "full_name_user_0054",
        ],
        "pi_platform_parent_message_id": [None] * 3,
        "pi_platform_root_message_id": [None] * 3,
        "pi_text": [  # noqa: E501
            "🔭 What international legal frameworks apply to digital conflict and digital harms in conflict settings?",  # noqa: E501
            "📢 Is your organisation exposed to hate speech online?",  # noqa: E501
            "A #BuildPeace2025 també vam obrir espais per escoltar experiències personals que ens ajuden a entendre millor els impactes dels conflictes i les formes de resistència que neixen a cada territori.",  # noqa: E501
        ],
        "pi_platform_message_url": [
            "https://www.instagram.com/p/code_0001/",
            "https://www.instagram.com/p/code_0008/",
            "https://www.instagram.com/p/code_0049/",
        ],
        "platform_message_last_updated_at": [
            datetime.utcfromtimestamp(1772184311),
            datetime.utcfromtimestamp(1771325514),
            datetime.utcfromtimestamp(1765276772),
        ],
        "like_count": [
            3,  # 3 + 0
            15,  # 15 + 0
            30,  # 29 + 1
        ],
        "share_count": [
            0,  # None -> 0
            1,
            1,
        ],
        "comment_count": [
            5,
            3,
            0,
        ],
    }

    df = pd.DataFrame(data)  # noqa: PD901
    df["gather_id"] = 9
    df["gather_batch_id"] = 3
    df["gather_type"] = gathers.schemas.ChildTypeName.danek_instagram_posts.value
    df["platform"] = gathers.schemas.Platform.instagram
    df["data_type"] = gathers.schemas.DataType.posts
    df["platform_message_last_updated_at"] = df["platform_message_last_updated_at"].dt.tz_localize(
        "UTC"
    )
    return coerce_validate_expected_df(df)


@pytest.fixture
def normalised_danek_instagram_comments_df() -> pd.DataFrame:
    """Return the expected DataFrame based on processed Instagram comments JSON data."""
    data = {
        "pi_platform_message_id": [
            "comment_0101",
            "comment_0001",
            "comment_0002",
            "comment_0003",
            "comment_0004",
            "comment_0005",
        ],
        "pi_platform_message_author_id": [
            "pk_user_0001",
            "pk_user_0011",
            "pk_user_0012",
            "pk_user_0013",
            "pk_user_0014",
            "pk_user_0015",
        ],
        "pi_platform_message_author_name": [
            "username_user_0001",
            "username_user_0011",
            "username_user_0012",
            "username_user_0013",
            "username_user_0014",
            "username_user_0015",
        ],
        "pi_platform_parent_message_id": [
            "post_0701",
        ]
        + ["post_0716"] * 5,
        "pi_platform_root_message_id": [
            "post_0701",
        ]
        + ["post_0716"] * 5,
        "pi_text": [
            "Un esdeveniment increïble ! Moltes gràcies username_user_0002! 😃🙌🌅",
            "Training",
            "Training",
            "TRAINING",
            "Training",
            "Training",
        ],
        "pi_platform_message_url": [None] * 6,
        "platform_message_last_updated_at": [
            datetime.utcfromtimestamp(ts)
            for ts in [
                1764847146,
                1773355693,
                1773195996,
                1773141417,
                1772962545,
                1772945832,
            ]
        ],
        "like_count": [
            2,
            1,
            0,
            0,
            0,
            0,
        ],
        "share_count": [0] * 6,
        "comment_count": [
            0,
            1,
            1,
            1,
            1,
            1,
        ],
    }

    comments_df = pd.DataFrame(data)
    comments_df["gather_id"] = 10
    comments_df["gather_batch_id"] = 3
    comments_df["gather_type"] = gathers.schemas.ChildTypeName.danek_instagram_comments.value
    comments_df["platform"] = gathers.schemas.Platform.instagram
    comments_df["data_type"] = gathers.schemas.DataType.comments

    # Ensure timestamps are UTC
    comments_df["platform_message_last_updated_at"] = comments_df[
        "platform_message_last_updated_at"
    ].dt.tz_localize("UTC")

    return coerce_validate_expected_df(comments_df)
