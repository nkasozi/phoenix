"""Keyword match classifier module."""

import dataclasses
import re

import prefect
from google.cloud import bigquery

from phiphi.api.projects.classifiers.keyword_match import schemas
from phiphi.config import settings
from phiphi.pipeline_jobs import constants as pipeline_jobs_constants


@dataclasses.dataclass
class KeywordMatchRegexConfig:
    """Configuration for a keyword match regex."""

    raw_must: str
    regex: str
    is_quoted: bool


PRE_WORD_BOUNDARY_STR = "(^|[^\\p{L}0-9_])"
POST_WORD_BOUNDARY_STR = "([^\\p{L}0-9_]|$)"


def create_keyword_match_regex_config(raw_must: str) -> list[KeywordMatchRegexConfig]:
    r"""Create a list of KeywordMatchRegexConfig from a raw must string.

    This function parses `raw_must` for tokens. Tokens can be separated by whitespace
    or enclosed in double-quotes to keep multi-word tokens together. For tokens
    enclosed in quotes, `is_quoted` is set to True, and we do not add word-boundaries
    in the resulting regex. For unquoted tokens, `is_quoted` is set to False and
    word-boundaries (`\\b`) are used in the regex to match whole words.

    Args:
        raw_must: A string containing quoted or unquoted keywords
        (e.g., 'apples "bananas oranges"').

    Returns:
        A list of KeywordMatchRegexConfig objects.
    """
    # Matches either a quoted group ("...") or an unquoted sequence of non-whitespace
    pattern = re.compile(r'"([^"]+)"|(\S+)')
    matches = pattern.findall(raw_must)

    configs = []
    for quoted, unquoted in matches:
        if quoted:
            pattern = re.escape(quoted)
            # Quoted token -> no word boundaries, exact match
            configs.append(
                KeywordMatchRegexConfig(
                    raw_must=quoted,
                    # case-insensitive and checks for language agnostic word boundaries +
                    # start/end of sentence
                    regex=rf"(?is){PRE_WORD_BOUNDARY_STR}{pattern}{POST_WORD_BOUNDARY_STR}",
                    is_quoted=True,
                )
            )
        else:
            pattern = re.escape(unquoted)
            # Unquoted token -> use word boundaries
            configs.append(
                KeywordMatchRegexConfig(
                    raw_must=unquoted,
                    # case-insensitive and checks for language agnostic word boundaries +
                    # start/end of sentence
                    regex=rf"(?is){PRE_WORD_BOUNDARY_STR}{pattern}{POST_WORD_BOUNDARY_STR}",
                    is_quoted=False,
                )
            )

    return configs


def _execute_batch_query(
    client: bigquery.Client,
    source_table_name: str,
    destination_table_name: str,
    classifier_id: int,
    classifier_version_id: int,
    job_run_id: int,
    select_statements: list[str],
    query_parameters: list[bigquery.ScalarQueryParameter],
) -> None:
    """Execute a batch insert query for classified messages.

    Args:
        client: BigQuery client instance.
        source_table_name: Full name of the source table with deduplicated messages.
        destination_table_name: Full name of the destination table for classified messages.
        classifier_id: ID of the classifier being used.
        classifier_version_id: Version ID of the classifier.
        job_run_id: ID of the current job run.
        select_statements: List of SELECT statements to UNION ALL together.
        query_parameters: List of BigQuery query parameters.
    """
    if not select_statements:
        return

    # Add common parameters for this batch
    batch_parameters = [
        bigquery.ScalarQueryParameter("classifier_id", "INT64", classifier_id),
        bigquery.ScalarQueryParameter("classifier_version_id", "INT64", classifier_version_id),
        bigquery.ScalarQueryParameter("job_run_id", "INT64", job_run_id),
    ] + query_parameters

    unclassified_messages_query = f"""
        WITH unclassified_messages AS (
            SELECT
                src.phoenix_platform_message_id,
                src.pi_text  -- Include pi_text so it can be used in WHERE conditions
            FROM
                `{source_table_name}` AS src
            LEFT JOIN
                `{destination_table_name}` AS dst
            ON
                src.phoenix_platform_message_id = dst.phoenix_platform_message_id
                AND dst.classifier_id = @classifier_id
                AND dst.classifier_version_id = @classifier_version_id
            WHERE
                dst.phoenix_platform_message_id IS NULL
        )
    """

    union_query = " UNION ALL ".join(select_statements)
    query = f"""
        INSERT INTO `{destination_table_name}`
        (
            classifier_id,
            classifier_version_id,
            class_name,
            phoenix_platform_message_id,
            job_run_id
        )
        {unclassified_messages_query}
        {union_query}
    """

    job_config = bigquery.QueryJobConfig(query_parameters=batch_parameters)
    query_job = client.query(query, job_config=job_config)
    query_job.result()


@dataclasses.dataclass
class ClassSelectStatement:
    """A select statement for a single class with its query parameters and keyword count."""

    select_statement: str
    query_parameters: list[bigquery.ScalarQueryParameter]
    keyword_count: int


def _build_class_select_statements(
    class_configs: list[schemas.ClassToKeywordConfig],
) -> list[ClassSelectStatement]:
    """Build select statements for each class configuration.

    Args:
        class_configs: List of ClassToKeywordConfig with 'class_name' and 'musts'.

    Returns:
        List of ClassSelectStatement objects, one per non-empty class config.
    """
    class_statements: list[ClassSelectStatement] = []

    for config_index, config in enumerate(class_configs):
        if not config["musts"]:
            continue

        query_parameters: list[bigquery.ScalarQueryParameter] = []
        keyword_params = []

        not_params = []
        nots_value = config.get("nots", "") or ""

        if config.get("is_regex", False):
            # Raw regex mode: use the entire musts/nots strings as RE2 regexes
            # without escaping or tokenization. The user controls their own flags.
            param_name = f"config_{config_index}_keyword_0"
            query_parameters.append(
                bigquery.ScalarQueryParameter(param_name, "STRING", config["musts"])
            )
            keyword_params.append(f"REGEXP_CONTAINS(pi_text, @{param_name})")
            keyword_count = 1

            if nots_value:
                nots_param = f"config_{config_index}_not_0"
                query_parameters.append(
                    bigquery.ScalarQueryParameter(nots_param, "STRING", nots_value)
                )
                not_params.append(f"NOT REGEXP_CONTAINS(pi_text, @{nots_param})")
                keyword_count += 1
        else:
            # Standard mode: tokenize and escape keywords
            keywords = create_keyword_match_regex_config(config["musts"])
            for i, keyword_config in enumerate(keywords):
                param_name = f"config_{config_index}_keyword_{i}"
                query_parameters.append(
                    bigquery.ScalarQueryParameter(param_name, "STRING", keyword_config.regex)
                )
                keyword_params.append(f"REGEXP_CONTAINS(pi_text, @{param_name})")
            keyword_count = len(keywords)

            if nots_value:
                not_keywords = create_keyword_match_regex_config(nots_value)
                for i, keyword_config in enumerate(not_keywords):
                    nots_param = f"config_{config_index}_not_{i}"
                    query_parameters.append(
                        bigquery.ScalarQueryParameter(nots_param, "STRING", keyword_config.regex)
                    )
                    not_params.append(f"NOT REGEXP_CONTAINS(pi_text, @{nots_param})")
                keyword_count += len(not_keywords)

        combined_conditions = " AND ".join(keyword_params + not_params)
        class_name_param = f"class_name_{config_index}"
        query_parameters.append(
            bigquery.ScalarQueryParameter(class_name_param, "STRING", config["class_name"])
        )

        select_statement = f"""
            SELECT
                @classifier_id AS classifier_id,
                @classifier_version_id AS classifier_version_id,
                @{class_name_param} AS class_name,
                phoenix_platform_message_id,
                @job_run_id AS job_run_id
            FROM
                unclassified_messages
            WHERE
                {combined_conditions}
            """

        class_statements.append(
            ClassSelectStatement(
                select_statement=select_statement,
                query_parameters=query_parameters,
                keyword_count=keyword_count,
            )
        )

    return class_statements


def _chunk_by_keyword_count(
    class_statements: list[ClassSelectStatement],
    keywords_per_batch: int,
) -> list[list[ClassSelectStatement]]:
    """Chunk class statements into batches respecting the keyword limit.

    Args:
        class_statements: List of ClassSelectStatement objects.
        keywords_per_batch: Maximum number of keywords per batch.

    Returns:
        List of batches, where each batch is a list of ClassSelectStatement objects.
    """
    if not class_statements:
        return []

    batches: list[list[ClassSelectStatement]] = []
    current_batch: list[ClassSelectStatement] = []
    current_keyword_count = 0

    for statement in class_statements:
        # If adding this statement would exceed the limit, start a new batch
        if (
            current_keyword_count > 0
            and current_keyword_count + statement.keyword_count > keywords_per_batch
        ):
            batches.append(current_batch)
            current_batch = []
            current_keyword_count = 0

        current_batch.append(statement)
        current_keyword_count += statement.keyword_count

    # Add the final batch if non-empty
    if current_batch:
        batches.append(current_batch)

    return batches


@prefect.task
def classify(
    classifier: schemas.KeywordMatchClassifierPipeline,
    bigquery_dataset: str,
    job_run_id: int,
    keywords_per_batch: int | None = None,
) -> None:
    """Classify messages using keyword match classifier through BigQuery query.

    This function batches keyword classifications into multiple queries to avoid
    BigQuery query complexity limits. Each batch processes up to keywords_per_batch
    keywords across all classes.

    Args:
        classifier: The keyword match classifier pipeline configuration.
        bigquery_dataset: The BigQuery dataset name.
        job_run_id: The ID of the current job run.
        keywords_per_batch: Maximum number of keywords per query batch. Defaults to
            settings.KEYWORD_MATCH_KEYWORDS_PER_BATCH.
    """
    if keywords_per_batch is None:
        keywords_per_batch = settings.KEYWORD_MATCH_KEYWORDS_PER_BATCH

    client = bigquery.Client()
    source_table_name = (
        f"{bigquery_dataset}."
        f"{pipeline_jobs_constants.DEDUPLICATED_GENERALISED_MESSAGES_TABLE_NAME}"
    )
    destination_table_name = (
        f"{bigquery_dataset}.{pipeline_jobs_constants.CLASSIFIED_MESSAGES_TABLE_NAME}"
    )

    # Build all select statements
    class_statements = _build_class_select_statements(
        classifier.latest_version.params["class_to_keyword_configs"]
    )

    # Chunk into batches by keyword count
    batches = _chunk_by_keyword_count(class_statements, keywords_per_batch)

    # Execute each batch
    for batch in batches:
        select_statements = [stmt.select_statement for stmt in batch]
        query_parameters = [param for stmt in batch for param in stmt.query_parameters]

        _execute_batch_query(
            client=client,
            source_table_name=source_table_name,
            destination_table_name=destination_table_name,
            classifier_id=classifier.id,
            classifier_version_id=classifier.latest_version.version_id,
            job_run_id=job_run_id,
            select_statements=select_statements,
            query_parameters=query_parameters,
        )
