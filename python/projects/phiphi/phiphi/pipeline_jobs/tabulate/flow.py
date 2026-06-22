"""Module containing the Prefect flow for tabulate."""

from typing import Coroutine

import prefect
from google.cloud import bigquery

from phiphi import constants
from phiphi.api.projects.job_runs import pipeline_job_result_schemas
from phiphi.pipeline_jobs import constants as pipeline_jobs_constants
from phiphi.pipeline_jobs.tabulate import quality_check


def escape_sql_value(value: str) -> str:
    """Escapes single quotes in a string for safe SQL queries."""
    return value.replace("'", "\\'")


@prefect.task
def tabulate_post_comment_connections(
    job_run_id: int,
    bigquery_dataset: str,
    active_classifiers_versions: list[tuple[int, int]],
) -> None:
    """Task which tabulates data connecting posts and comments.

    The tabulate flow must produce a table that matches the schema the file `tabulated_messages.py`
    and in the notion manual
    https://howtobuildup.notion.site/Gathered-data-output-all-platforms-9bf3ac6ccc824dfca2fe8fa3d7393e64.

    Args:
        job_run_id (int): The job run id.
        bigquery_dataset (str): The bigquery dataset to use.
        active_classifiers_versions (list[tuple[int, int]]): The active classifiers versions to
            use. Each tuple should be (classifier_id, version_id).
    """
    client = bigquery.Client()

    source_table_name = f"{bigquery_dataset}.{pipeline_jobs_constants.DEDUPLICATED_GENERALISED_MESSAGES_TABLE_NAME}"  # noqa: E501
    tabulate_table_name = (
        f"{bigquery_dataset}.{pipeline_jobs_constants.TABULATED_MESSAGES_TABLE_NAME}"
    )
    classified_messages_table_name = (
        f"{bigquery_dataset}.{pipeline_jobs_constants.CLASSIFIED_MESSAGES_TABLE_NAME}"
    )
    classified_authors_table_name = (
        f"{bigquery_dataset}.{pipeline_jobs_constants.CLASSIFIED_AUTHORS_TABLE_NAME}"
    )

    # Note, we could convert the classifier dicts into their pydantic models, and then get type
    # checking on `id` and `version_id`, but this makes testing harder as we need to create entire
    # classifier objects instead of just minimal dicts.
    # Note we always add `(NULL, NULL)` to handle the case where there are no classifiers.
    classifier_ids = ", ".join(
        ["(NULL, NULL)"] + [f"({t[0]}, {t[1]})" for t in active_classifiers_versions]
    )

    tabulate_query = f"""
    CREATE OR REPLACE TABLE `{tabulate_table_name}` AS
    WITH active_only_classified_authors AS (
        SELECT DISTINCT
            classifier_id,
            classifier_version_id,
            phoenix_platform_message_author_id,
            class_name
        FROM `{classified_authors_table_name}`
        WHERE (classifier_id, classifier_version_id) IN ({classifier_ids})
    ),
    active_only_classified_messages AS (
        SELECT DISTINCT
            classifier_id,
            classifier_version_id,
            phoenix_platform_message_id,
            class_name
        FROM `{classified_messages_table_name}`
        WHERE (classifier_id, classifier_version_id) IN ({classifier_ids})
    ),
    messages_classes AS (
        SELECT
            m.*,
            cm.class_name AS class,
            mca.class_name AS author_class_name,
        FROM
            `{source_table_name}` m
        LEFT JOIN
            active_only_classified_messages cm
        ON
            m.phoenix_platform_message_id = cm.phoenix_platform_message_id
        LEFT JOIN
            active_only_classified_authors mca
        ON
            m.phoenix_platform_message_author_id = mca.phoenix_platform_message_author_id
    ),
    posts AS (
        SELECT
            *
        FROM
            messages_classes
        WHERE
            data_type = 'posts'
    ),
    comments AS (
        SELECT
            *
        FROM
            messages_classes
        WHERE
            data_type = 'comments'
    ),
    orphan_comments AS (
        SELECT c.*
        FROM comments c
        LEFT JOIN posts p
        ON p.phoenix_platform_message_id = c.phoenix_platform_root_message_id
        WHERE p.phoenix_platform_message_id IS NULL
    )
    SELECT
        p.platform AS platform,

        -- Post Author
        -- Currently many columns not implemented (i.e. NULL)
        CAST(NULL AS STRING) AS post_author_category,
        p.author_class_name AS post_author_class,
        CAST(NULL AS STRING) AS post_author_description_pi,
        CAST(NULL AS INT64) AS post_author_followers_count,
        p.phoenix_platform_message_author_id AS post_author_id,
        CAST(NULL AS STRING) AS post_author_location,
        p.pi_platform_message_author_name AS post_author_name_pi,
        CAST(NULL AS STRING) AS post_author_link_pi,

        -- Post
        p.class AS post_class,
        p.comment_count AS post_comment_count,
        DATE(p.platform_message_last_updated_at) AS post_date,
        p.platform_message_last_updated_at AS post_datetime,
        p.gather_id AS post_gather_id,
        p.phoenix_platform_message_id AS post_id,
        p.like_count AS post_like_count,
        p.pi_platform_message_url AS post_link_pi,
        p.share_count AS post_share_count,
        p.pi_text AS post_text_pi,
        p.pi_platform_message_id AS post_platform_id_pi,

        -- Comment Author
        c.author_class_name AS comment_author_class,
        c.phoenix_platform_message_author_id AS comment_author_id,
        c.pi_platform_message_author_name AS comment_author_name_pi,

        -- Comment
        c.class AS comment_class,
        DATE(c.platform_message_last_updated_at) AS comment_date,
        c.platform_message_last_updated_at AS comment_datetime,
        c.gather_id AS comment_gather_id,
        c.phoenix_platform_message_id AS comment_id,
        c.like_count AS comment_like_count,
        c.pi_platform_message_url AS comment_link_pi,
        c.phoenix_platform_root_message_id AS comment_parent_post_id,
        c.phoenix_platform_parent_message_id AS comment_replied_to_id,
        c.pi_text AS comment_text_pi,

        -- Platform specific stats
        -- Facebook
        CAST(NULL AS INT64) AS facebook_video_views,
        -- TikTok
        CAST(p.tiktok_post_plays AS INT64) AS tiktok_post_plays,
        -- X
        p.x_post_retweeted_id AS x_post_retweeted_id,
        CAST(c.x_is_quote AS BOOL) AS x_comment_is_quote,
        CAST(c.x_is_reply AS BOOL) AS x_comment_is_reply,

        -- Developer fields should always be last
        -- Using CURRENT_TIMESTAMP rather then PARSE_TIMESTAMP as it seems to make the integration
        -- tests faster.
        CURRENT_TIMESTAMP() AS phoenix_processed_at,
        {job_run_id} AS phoenix_job_run_id
    FROM
        posts p
    LEFT JOIN
        comments c
    ON
        p.phoenix_platform_message_id = c.phoenix_platform_root_message_id

    UNION ALL

    -- 2) Orphan comments (no matching post). Post_* fields are NULL.
    SELECT
        c.platform AS platform,

        -- Post Author
        CAST(NULL AS STRING) AS post_author_category,
        CAST(NULL AS STRING) AS post_author_class,
        CAST(NULL AS STRING) AS post_author_description_pi,
        CAST(NULL AS INT64) AS post_author_followers_count,
        CAST(NULL AS STRING) AS post_author_id,
        CAST(NULL AS STRING) AS post_author_location,
        CAST(NULL AS STRING) AS post_author_name_pi,
        CAST(NULL AS STRING) AS post_author_link_pi,

        -- Post
        CAST(NULL AS STRING) AS post_class,
        CAST(NULL AS INT64) AS post_comment_count,
        CAST(NULL AS DATE) AS post_date,
        CAST(NULL AS TIMESTAMP) AS post_datetime,
        CAST(NULL AS INT64) AS post_gather_id,
        CAST(NULL AS STRING) AS post_id,
        CAST(NULL AS INT64) AS post_like_count,
        CAST(NULL AS STRING) AS post_link_pi,
        CAST(NULL AS INT64) AS post_share_count,
        CAST(NULL AS STRING) AS post_text_pi,
        CAST(NULL AS STRING) AS post_platform_id_pi,

        -- Comment Author
        c.author_class_name AS comment_author_class,
        c.phoenix_platform_message_author_id AS comment_author_id,
        c.pi_platform_message_author_name AS comment_author_name_pi,

        -- Comment
        c.class AS comment_class,
        DATE(c.platform_message_last_updated_at) AS comment_date,
        c.platform_message_last_updated_at AS comment_datetime,
        c.gather_id AS comment_gather_id,
        c.phoenix_platform_message_id AS comment_id,
        c.like_count AS comment_like_count,
        c.pi_platform_message_url AS comment_link_pi,
        c.phoenix_platform_root_message_id AS comment_parent_post_id,
        c.phoenix_platform_parent_message_id AS comment_replied_to_id,
        c.pi_text AS comment_text_pi,

        -- Platform specific stats (post-only metrics are NULL for orphans)
        CAST(NULL AS INT64) AS facebook_video_views,
        CAST(NULL AS INT64) AS tiktok_post_plays,
        CAST(NULL AS STRING) AS x_post_retweeted_id,
        CAST(c.x_is_quote AS BOOL) AS x_comment_is_quote,
        CAST(c.x_is_reply AS BOOL) AS x_comment_is_reply,

        -- Developer fields
        CURRENT_TIMESTAMP() AS phoenix_processed_at,
        {job_run_id} AS phoenix_job_run_id
    FROM orphan_comments c
    """

    tabulate_job = client.query(tabulate_query)
    tabulate_job.result()


@prefect.task
def tabulate_post_post_class_connections(
    bigquery_dataset: str,
) -> None:
    """Task which tabulates data connecting posts' classes.

    This task self-joins the table made by `tabulate_post_comment_connections` task to create a
    table which has the post_class and post_class_2 columns. These allow users to visualise
    connections between multiple classes of a post. It only uses a subset of the columns to
    minimize table size/costs. Most notably the pi_text column is not included.

    Args:
        bigquery_dataset (str): The bigquery dataset to use.
    """
    client = bigquery.Client()
    tabulate_table_name = (
        f"{bigquery_dataset}.{pipeline_jobs_constants.TABULATED_MESSAGES_TABLE_NAME}"
    )
    post_post_class_connection_table_name = (
        f"{bigquery_dataset}.{pipeline_jobs_constants.POST_POST_CLASS_CONNECTION_TABLE_NAME}"
    )

    tabulate_query = f"""
    CREATE OR REPLACE TABLE `{post_post_class_connection_table_name}` AS
    SELECT
      MAX(a.platform) as platform,
      MAX(a.post_author_category) as post_author_category,
      MAX(a.post_author_class) as post_author_class,
      MAX(a.post_author_id) as post_author_id,
      MAX(a.post_author_name_pi) as post_author_name_pi,
      MAX(a.post_author_link_pi) as post_author_link_pi,
      a.post_class,
      MAX(a.post_comment_count) as post_comment_count,
      MAX(a.post_date) as post_date,
      MAX(a.post_datetime) as post_datetime,
      MAX(a.post_link_pi) as post_link_pi,
      MAX(a.post_like_count) as post_like_count,
      MAX(a.post_share_count) as post_share_count,
      MAX(a.post_text_pi) as post_text_pi,
      MAX(a.post_platform_id_pi) as post_platform_id_pi,
      MAX(a.facebook_video_views) as facebook_video_views,
      MAX(a.tiktok_post_plays) as tiktok_post_plays,
      MAX(a.x_post_retweeted_id) as x_post_retweeted_id,
      -- We do not include comment fields as they are not needed for post-post connections
      b.post_class AS post_class_2
    FROM
      `{tabulate_table_name}` a
    LEFT JOIN
      `{tabulate_table_name}` b
    ON
      a.post_id = b.post_id
    -- Only include rows where both sides of the join have a post_id (i.e. ignore orphan comments)
    WHERE
      a.post_id IS NOT NULL
      AND b.post_id IS NOT NULL
    GROUP BY
      a.post_id,
      a.post_class,
      b.post_class;
    """
    tabulate_job = client.query(tabulate_query)
    tabulate_job.result()


def tabulate_comment_comment_class_connections(
    bigquery_dataset: str,
) -> None:
    """Task which tabulates data connecting comments' classes.

    This task self-joins the table made by `tabulate_post_comment_connections` task to create a
    table which has the comment_class and comment_class_2 columns. These allow users to visualise
    connections between multiple classes of a comment. It only uses a subset of the columns to
    minimize table size/costs. Most notably the pi_text column is not included.

    Args:
        bigquery_dataset (str): The bigquery dataset to use.
    """
    client = bigquery.Client()
    tabulate_table_name = (
        f"{bigquery_dataset}.{pipeline_jobs_constants.TABULATED_MESSAGES_TABLE_NAME}"
    )
    comment_comment_class_connection_table_name = (
        f"{bigquery_dataset}.{pipeline_jobs_constants.COMMENT_COMMENT_CLASS_CONNECTION_TABLE_NAME}"
    )

    tabulate_query = f"""
    CREATE OR REPLACE TABLE `{comment_comment_class_connection_table_name}` AS
    SELECT
      MAX(a.platform) AS platform,
      MAX(a.post_author_category) AS post_author_category,
      MAX(a.post_author_class) AS post_author_class,
      MAX(a.post_author_id) AS post_author_id,
      MAX(a.post_author_link_pi) AS post_author_link_pi,
      MAX(a.post_class) AS post_class,
      MAX(a.post_comment_count) AS post_comment_count,
      MAX(a.post_date) AS post_date,
      MAX(a.post_datetime) AS post_datetime,
      MAX(a.post_link_pi) AS post_link_pi,
      MAX(a.post_like_count) AS post_like_count,
      MAX(a.post_share_count) AS post_share_count,
      MAX(a.facebook_video_views) AS facebook_video_views,
      MAX(a.tiktok_post_plays) AS tiktok_post_plays,
      MAX(a.x_post_retweeted_id) AS x_post_retweeted_id,
      MAX(a.comment_author_class) AS comment_author_class,
      MAX(a.comment_author_id) AS comment_author_id,
      MAX(a.comment_author_name_pi) AS comment_author_name_pi,
      a.comment_class,
      b.comment_class AS comment_class_2,
      MAX(a.comment_date) AS comment_date,
      MAX(a.comment_datetime) AS comment_datetime,
      MAX(a.comment_like_count) AS comment_like_count,
      MAX(a.comment_link_pi) AS comment_link_pi,
      MAX(a.comment_text_pi) AS comment_text_pi,
      MAX(a.x_comment_is_quote) AS x_comment_is_quote
    FROM
      `{tabulate_table_name}` a
    LEFT JOIN
      `{tabulate_table_name}` b
    ON
      a.comment_id = b.comment_id
    GROUP BY
      a.comment_id,
      a.comment_class,
      b.comment_class;
    """
    tabulate_job = client.query(tabulate_query)
    tabulate_job.result()


@prefect.flow(name="tabulate_flow")
def tabulate_flow(
    job_run_id: int,
    project_namespace: str,
    active_classifiers_versions: list[tuple[int, int]],
) -> pipeline_job_result_schemas.PipelineJobResult:
    """Flow which tabulates data - producing the dataset for the dashboard to use."""
    tabulate_post_comment_connections(
        job_run_id=job_run_id,
        bigquery_dataset=project_namespace,
        active_classifiers_versions=active_classifiers_versions,
    )
    tabulate_post_post_class_connections(bigquery_dataset=project_namespace)
    tabulate_comment_comment_class_connections(bigquery_dataset=project_namespace)
    quality_check.run_quality_checks(bigquery_dataset=project_namespace)
    return pipeline_job_result_schemas.PipelineJobResult()


def create_deployments(
    override_work_pool_name: str | None = None,
    deployment_name_prefix: str = "",
    image: str = constants.DEFAULT_IMAGE,
    tags: list[str] = [],
    build: bool = False,
    push: bool = False,
) -> list[Coroutine]:
    """Create deployments for flow_runner_flow.

    Args:
        override_work_pool_name (str | None): The name of the work pool to use to override the
        default work pool.
        deployment_name_prefix (str, optional): The prefix of the deployment name. Defaults to "".
        image (str, optional): The image to use for the deployments. Defaults to
        constants.DEFAULT_IMAGE.
        tags (list[str], optional): The tags to use for the deployments. Defaults to [].
        build (bool, optional): If True, build the image. Defaults to False.
        push (bool, optional): If True, push the image. Defaults to False.

    Returns:
        list[Coroutine]: List of coroutines that create deployments.
    """
    work_pool_name = str(constants.WorkPool.main)
    if override_work_pool_name:
        work_pool_name = override_work_pool_name
    task = tabulate_flow.deploy(
        name=deployment_name_prefix + tabulate_flow.name,
        work_pool_name=work_pool_name,
        image=image,
        build=build,
        push=push,
        tags=tags,
    )

    return [task]
