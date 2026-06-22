"""Test keyword match classifier."""

import datetime

import pandas as pd
import pandas_gbq
import pytest

from phiphi.pipeline_jobs import constants as pipeline_jobs_constants
from phiphi.pipeline_jobs import generalised_messages
from phiphi.pipeline_jobs import utils as pipeline_jobs_utils
from phiphi.pipeline_jobs.classify import flow as classify_flow


@pytest.mark.asyncio
async def test_keyword_match_classifier(tmp_bq_project):
    """Test the keyword match classifier."""
    test_project_namespace = tmp_bq_project

    # Create dummy data to insert into BigQuery that conforms to the table schema
    test_cases: list[tuple[str, str, list[str]]] = [
        ("I love apples and bananas.", "a", ["apple_banana"]),
        ("I love apples and orange's.", "b", ["apple_orange"]),
        ("I love orange's and bananas.", "c", ["orange banana"]),
        ("I love orange's and apples.", "d", ["apple_orange"]),
        ("I love bananas and furthermore I \n love puppies.", "e", ["phrase"]),
        ("Puppies furthermore, kittens.", "f", []),
        # "greenapples and oranges" should not match "apples oranges"
        ("I love greenapples and orange's", "g", []),
        # "green-apples and oranges" does match "apples oranges" as hyphen is a word-boundary in
        # google bigquery. Note that this is not the case in regular regex.
        ("I love green-apples and orange's.", "h", ["apple_orange"]),
        ("fds ጋላ ታሪክ የለው ታሪክ ያጠፋል አማራ ይሄን ጋላ ለአንዴና ለመጨረሻ", "i", ["non_latin_quotes", "non_latin"]),
        ("التفاح الذي احبه", "j", ["apples_arabic"]),
        ("نص التفاح تجريبي", "k", ["apples_arabic"]),  # "Apples" in the middle in Arabic
        ("نص الذي التفاح", "l", ["apples_arabic"]),  # "Apples" at the end in Arabic
        ("هذا اختبار", "m", []),  ## "This is a test" in Arabic
        (
            "I love green-apples and ora\\nge's.",
            "n",
            ["backslash_test", "backslash_phrase_test"],
        ),  # Test for backslash in the regex in the text
        # is_regex: leetspeak pattern should match obfuscated text
        ("Die g3nderw4hn ist überall.", "o", ["regex_leetspeak", "regex_nots"]),
        # is_regex: leetspeak pattern should NOT match unrelated text
        ("This is a normal sentence.", "p", []),
        # is_regex: case-sensitive regex "Apples" only matches capital-A "Apples".
        # Lowercase "apples" in other messages (a, b, d, etc.) must NOT match this class,
        # verifying that is_regex passes the pattern through without adding (?i).
        (
            "I love Apples and g3nderwahn.",
            "q",
            ["apple_regex_mix", "regex_leetspeak", "regex_nots"],
        ),
        # is_regex nots: matches musts regex but excluded by nots regex
        ("Die g3nderw4hn ist satirisch.", "r", ["regex_leetspeak"]),
        # is_regex nots: matches musts regex and nots regex, so excluded from regex_nots class
        ("Die g3nderw4hn ist satirisch und harmlos.", "s", ["regex_leetspeak"]),
        # is_regex nots: matches musts regex, does not match nots regex, so included
        ("Die g3nderw4hn ist gefährlich.", "t", ["regex_leetspeak", "regex_nots"]),
        ("I love bananas and apples.", "last_one", ["apple_banana"]),
    ]

    # Separate texts and IDs from pairs, limiting to requested number of examples
    texts, message_ids, classes = zip(*test_cases)

    # Create DataFrame
    test_df = pd.DataFrame(
        {"phoenix_platform_message_id": message_ids, "pi_text": texts, "classes": classes}
    )
    # Create the full test data
    deduped_general_messages_df = generalised_messages.create_example(test_df.shape[0])
    deduped_general_messages_df["pi_text"] = test_df["pi_text"]
    deduped_general_messages_df["phoenix_platform_message_id"] = test_df[
        "phoenix_platform_message_id"
    ]

    # Add all but the last message to the database as the first set
    partial_messages_df = deduped_general_messages_df.iloc[:-1]

    validated_partial_messages_df = generalised_messages.validate(partial_messages_df)

    partial_df = test_df.iloc[:-1]

    classifier_id = 1
    classifier_version_id = 1
    job_run_id = 9

    # Build the expected_classified_messages_df from the list of classes
    flattened_data = []
    for _, row in partial_df.iterrows():
        msg_id = row["phoenix_platform_message_id"]
        # Go through each class in the 'classes' list for that message
        for single_class in row["classes"]:
            flattened_data.append(
                {
                    "classifier_id": classifier_id,
                    "classifier_version_id": classifier_version_id,
                    "class_name": single_class,
                    "phoenix_platform_message_id": msg_id,
                    "job_run_id": job_run_id,
                    "class_probability": 1.0,
                }
            )

    expected_classified_messages_df = pd.DataFrame(flattened_data)

    pipeline_jobs_utils.write_data(
        df=validated_partial_messages_df,
        dataset=test_project_namespace,
        table=pipeline_jobs_constants.DEDUPLICATED_GENERALISED_MESSAGES_TABLE_NAME,
    )

    # Step 2: Instantiate the KeywordMatchClassifierPipeline to match the test data.
    # Id "f" and "g" should not match a class, the rest should
    # We also bypass ruff formatting here to allow for escaped doublequotes
    # fmt: off
    classifier = {
        "id": classifier_id,
        "project_id": 10,
        "name": "test_classifier",
        "description": "Test keyword match classifier",
        "type": "keyword_match",
        "latest_version": {
            "version_id": classifier_version_id,
            "classifier_id": classifier_id,
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now(),
            "classes": [
                {"name": "apple_banana", "description": "Things that are apples and bananas"},
                {"name": "apple_orange", "description": "Things that are apples and orange's"},
                {"name": "orange banana", "description": "Things that are orange's and bananas"},
                {"name": "phrase", "description": "a specific phrase"},
                {"name": "non_latin_quotes", "description": "non-latin characters"},
                {"name": "non_latin", "description": "non-latin characters"},
                {"name": "apples_arabic", "description": "Things that are apples and arabic"},
                {"name": "backslash_test", "description": "Things with a backslash"},
                {"name": "backslash_phrase_test", "description": "Things with a backslash"},
                {"name": "regex_leetspeak", "description": "Leetspeak regex match"},
                {"name": "apple_regex_mix", "description": "Apples matched by standard keyword"},
                {"name": "regex_nots", "description": "Leetspeak regex with nots exclusion"},
            ],
            "params": {
                "class_to_keyword_configs": [
                    {"class_name": "apple_banana", "musts": "apples bananas"},
                    # It is important to test for keywords with `'` in them so that we are doing a
                    # simple check that SQL injection is not happening. A full one is not needed as
                    # we use the bigquery parameters to prevent the injection in the query.
                    {"class_name": "apple_orange", "musts": "apples orange's"},
                    # Orange banana has a space in to check that class names with a space are
                    # supported.
                    {"class_name": "orange banana", "musts": "orange's bananas"},
                    # Test for a phrase, including escaped double quotes Test for a phrase,
                    # including escaped double quotes as this is what will be sent down the
                    # pipeline from the console
                    {"class_name": "phrase", "musts": "\"and furthermore\""},  # noqa: Q000
                    {"class_name": "not_included", "musts": ""},
                    {"class_name": "non_latin_quotes", "musts": "\"ጋላ\""},
                    # Unfortunately non Latin with word boundaries is not working.
                    {"class_name": "non_latin", "musts": "ጋላ"},
                    {"class_name": "apples_arabic", "musts": "التفاح"},
                    {"class_name": "backslash_test", "musts": "ora\\nge"},
                    {"class_name": "backslash_phrase_test", "musts": "and ora\\nge"},
                    # is_regex: leetspeak pattern with user-supplied
                    # (?i) for case-insensitive matching
                    {"class_name": "regex_leetspeak", "musts": "(?i)[g9][e3]nd[e3]rw[a@4]hn", "is_regex": True},  # noqa: E501
                    # is_regex: case-sensitive "Apples" — only matches
                    # capital-A, not lowercase "apples"
                    {"class_name": "apple_regex_mix", "musts": "Apples", "is_regex": True},
                    # is_regex with nots: matches leetspeak but excludes "satirisch" or "harmlos"
                    {"class_name": "regex_nots", "musts": "(?i)[g9][e3]nd[e3]rw[a@4]hn", "nots": "(?i)satirisch|harmlos", "is_regex": True},  # noqa: E501
                ]
            },
        },
    }
    # fmt:on

    # Step 3: Run the classifier for the first time
    await classify_flow.classify_flow(
        classifier_dict=classifier, project_namespace=test_project_namespace, job_run_id=job_run_id
    )

    # Step 4: Check the classified messages table
    classified_messages_df = pandas_gbq.read_gbq(
        f"SELECT * "
        f"FROM {test_project_namespace}.{pipeline_jobs_constants.CLASSIFIED_MESSAGES_TABLE_NAME}"
    )

    # pd.testing using check_like=True doesn't work due to dtypes, so we'll use set comparison
    set1 = set(classified_messages_df.itertuples(index=False, name=None))
    set2 = set(expected_classified_messages_df.itertuples(index=False, name=None))
    assert set1 == set2, "DataFrames contain different rows after first classification"

    # Step 5: Add the remaining message to the database (the last row)
    remaining_message_df = deduped_general_messages_df.iloc[6:]
    validated_remaining_message_df = generalised_messages.validate(remaining_message_df)

    pipeline_jobs_utils.write_data(
        df=validated_remaining_message_df,
        dataset=test_project_namespace,
        table=pipeline_jobs_constants.DEDUPLICATED_GENERALISED_MESSAGES_TABLE_NAME,
    )

    # Step 6: Check classifier is incremental - i.e. running the same classifier again should not
    # duplicate the classified messages, and should classify all new messages (the last one)
    await classify_flow.classify_flow(
        classifier_dict=classifier, project_namespace=test_project_namespace, job_run_id=10
    )

    # Step 7: Check the classified messages table after rerun
    post_rerun_classified_messages_df = pandas_gbq.read_gbq(
        f"SELECT * "
        f"FROM {test_project_namespace}.{pipeline_jobs_constants.CLASSIFIED_MESSAGES_TABLE_NAME}"
    )

    # Update the expected DataFrame to include the last message
    new_message_df = pd.DataFrame(
        {
            "classifier_id": [1],
            "classifier_version_id": [1],
            "class_name": ["apple_banana"],
            "phoenix_platform_message_id": ["last_one"],
            "job_run_id": [10],
            "class_probability": [1.0],
        }
    )

    expected_classified_messages_df = pd.concat(
        [expected_classified_messages_df, new_message_df], ignore_index=True
    )

    set3 = set(post_rerun_classified_messages_df.itertuples(index=False, name=None))
    set4 = set(expected_classified_messages_df.itertuples(index=False, name=None))
    assert set3 == set4, "DataFrames contain different rows after adding the last message"
