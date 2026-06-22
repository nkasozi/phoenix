"""Test gather_classify_tabulate_flow.py."""

from unittest import mock

import pytest

from phiphi.api.projects.classifiers.keyword_match import schemas as keyword_match_schemas
from phiphi.pipeline_jobs.classify import keyword_match_classifier as kms


@pytest.mark.parametrize(
    "raw_must, expected",
    [
        (
            "apples bananas oranges",
            [
                kms.KeywordMatchRegexConfig(
                    "apples",
                    f"(?is){kms.PRE_WORD_BOUNDARY_STR}apples{kms.POST_WORD_BOUNDARY_STR}",
                    False,
                ),
                kms.KeywordMatchRegexConfig(
                    "bananas",
                    f"(?is){kms.PRE_WORD_BOUNDARY_STR}bananas{kms.POST_WORD_BOUNDARY_STR}",
                    False,
                ),
                kms.KeywordMatchRegexConfig(
                    "oranges",
                    f"(?is){kms.PRE_WORD_BOUNDARY_STR}oranges{kms.POST_WORD_BOUNDARY_STR}",
                    False,
                ),
            ],
        ),
        (
            'apples "bananas oranges"',
            [
                kms.KeywordMatchRegexConfig(
                    # Written regex rather than using f-string to make sure that it is correct
                    "apples",
                    "(?is)(^|[^\\p{L}0-9_])apples([^\\p{L}0-9_]|$)",
                    False,
                ),
                kms.KeywordMatchRegexConfig(
                    # Written regex rather than using f-string to make sure that it is correct
                    "bananas oranges",
                    # The `re` module escapes spaces in user input, though unnecessary, as a side
                    # effect of escaping special characters.
                    "(?is)(^|[^\\p{L}0-9_])bananas\\ oranges([^\\p{L}0-9_]|$)",
                    True,
                ),
            ],
        ),
        (
            '"apples bananas" oranges',
            [
                kms.KeywordMatchRegexConfig(
                    "apples bananas",
                    # The `re` module escapes spaces in user input, though unnecessary, as a side
                    # effect of escaping special characters.
                    (
                        f"(?is){kms.PRE_WORD_BOUNDARY_STR}"
                        "apples\\ bananas"
                        f"{kms.POST_WORD_BOUNDARY_STR}"
                    ),
                    True,
                ),
                kms.KeywordMatchRegexConfig(
                    "oranges",
                    f"(?is){kms.PRE_WORD_BOUNDARY_STR}oranges{kms.POST_WORD_BOUNDARY_STR}",
                    False,
                ),
            ],
        ),
        (
            # Non latin
            # fmt: off
            '"🍎" 🍌 🍊',
            # fmt: on
            [
                kms.KeywordMatchRegexConfig(
                    "🍎", f"(?is){kms.PRE_WORD_BOUNDARY_STR}🍎{kms.POST_WORD_BOUNDARY_STR}", True
                ),
                kms.KeywordMatchRegexConfig(
                    "🍌", f"(?is){kms.PRE_WORD_BOUNDARY_STR}🍌{kms.POST_WORD_BOUNDARY_STR}", False
                ),
                kms.KeywordMatchRegexConfig(
                    "🍊", f"(?is){kms.PRE_WORD_BOUNDARY_STR}🍊{kms.POST_WORD_BOUNDARY_STR}", False
                ),
            ],
        ),
        (
            # Arabic
            "تفاح موز برتقال",
            [
                kms.KeywordMatchRegexConfig(
                    "تفاح",
                    f"(?is){kms.PRE_WORD_BOUNDARY_STR}تفاح{kms.POST_WORD_BOUNDARY_STR}",
                    False,
                ),
                kms.KeywordMatchRegexConfig(
                    "موز",
                    f"(?is){kms.PRE_WORD_BOUNDARY_STR}موز{kms.POST_WORD_BOUNDARY_STR}",
                    False,
                ),
                kms.KeywordMatchRegexConfig(
                    "برتقال",
                    f"(?is){kms.PRE_WORD_BOUNDARY_STR}برتقال{kms.POST_WORD_BOUNDARY_STR}",
                    False,
                ),
            ],
        ),
        (
            # Arabic with quotes
            # fmt: off
            '"تفاح موز" برتقال',
            # fmt: on
            [
                kms.KeywordMatchRegexConfig(
                    "تفاح موز",
                    # The `re` module escapes spaces in user input, though unnecessary, as a side
                    # effect of escaping special characters.
                    f"(?is){kms.PRE_WORD_BOUNDARY_STR}تفاح\\ موز{kms.POST_WORD_BOUNDARY_STR}",
                    True,
                ),
                kms.KeywordMatchRegexConfig(
                    "برتقال",
                    f"(?is){kms.PRE_WORD_BOUNDARY_STR}برتقال{kms.POST_WORD_BOUNDARY_STR}",
                    False,
                ),
            ],
        ),
    ],
)
def test_create_regex_config(raw_must, expected):
    """Test create_regex_config."""
    assert kms.create_keyword_match_regex_config(raw_must) == expected


@pytest.mark.parametrize(
    "class_configs,keywords_per_batch,expected_batch_count",
    [
        # Single class with 3 keywords, batch size 100 -> 1 batch
        (
            [{"class_name": "class1", "musts": "word1 word2 word3"}],
            100,
            1,
        ),
        # Single class with 3 keywords, batch size 2 -> 2 batches
        # (first batch has 0 keywords, so class with 3 keywords goes into batch 1,
        # then final batch executes with that class)
        (
            [{"class_name": "class1", "musts": "word1 word2 word3"}],
            2,
            1,
        ),
        # Two classes, each with 2 keywords, batch size 3 -> 2 batches
        # (first class fits, second class would exceed limit, so flush first batch)
        (
            [
                {"class_name": "class1", "musts": "word1 word2"},
                {"class_name": "class2", "musts": "word3 word4"},
            ],
            3,
            2,
        ),
        # Three classes, batch size 5 -> 2 batches
        # class1 (2 keywords) + class2 (2 keywords) = 4, fits in batch 1
        # class3 (2 keywords) would make it 6, exceeds 5, so flush batch 1
        # class3 goes into batch 2
        (
            [
                {"class_name": "class1", "musts": "a b"},
                {"class_name": "class2", "musts": "c d"},
                {"class_name": "class3", "musts": "e f"},
            ],
            5,
            2,
        ),
        # Empty musts should be skipped
        (
            [
                {"class_name": "class1", "musts": "word1 word2"},
                {"class_name": "class2", "musts": ""},
                {"class_name": "class3", "musts": "word3"},
            ],
            100,
            1,
        ),
        # All empty musts -> 0 batches (no queries executed)
        (
            [
                {"class_name": "class1", "musts": ""},
                {"class_name": "class2", "musts": ""},
            ],
            100,
            0,
        ),
    ],
)
@mock.patch.object(kms, "_execute_batch_query")
@mock.patch("phiphi.pipeline_jobs.classify.keyword_match_classifier.bigquery.Client")
def test_classify_batching(
    mock_client_class,
    mock_execute_batch,
    class_configs,
    keywords_per_batch,
    expected_batch_count,
):
    """Test that classify correctly batches keywords into multiple queries."""
    # Create a mock classifier
    mock_classifier = mock.MagicMock()
    mock_classifier.id = 1
    mock_classifier.latest_version.version_id = 1
    mock_classifier.latest_version.params = {"class_to_keyword_configs": class_configs}

    # Call classify with the test configuration
    kms.classify.fn(
        classifier=mock_classifier,
        bigquery_dataset="test_dataset",
        job_run_id=123,
        keywords_per_batch=keywords_per_batch,
    )

    # Verify the correct number of batch queries were executed
    assert mock_execute_batch.call_count == expected_batch_count


def test_build_class_select_statements_is_regex_complex_pattern():
    """Test _build_class_select_statements with a complex regex (e.g. leetspeak)."""
    class_configs: list[keyword_match_schemas.ClassToKeywordConfig] = [
        {
            "class_name": "hate_speech",
            "musts": "(?i)[g9][e3]nd[e3]rw[a@4]hn",
            "is_regex": True,
        },
    ]
    results = kms._build_class_select_statements(class_configs)
    assert len(results) == 1
    stmt = results[0]
    # is_regex path should produce keyword_count=1
    assert stmt.keyword_count == 1
    # The regex should be passed through without escaping or tokenization
    assert len(stmt.query_parameters) == 2  # one for regex, one for class_name
    regex_param = stmt.query_parameters[0]
    assert regex_param.value == "(?i)[g9][e3]nd[e3]rw[a@4]hn"
    assert "REGEXP_CONTAINS" in stmt.select_statement


def test_build_class_select_statements_mixed_is_regex_and_standard():
    """Test mixed configs: some is_regex=True and some standard (is_regex=False)."""
    class_configs: list[keyword_match_schemas.ClassToKeywordConfig] = [
        {
            "class_name": "regex_class",
            "musts": "(?i)f[o0]+bar",
            "is_regex": True,
        },
        {
            "class_name": "standard_class",
            "musts": "apples bananas",
        },
    ]
    results = kms._build_class_select_statements(class_configs)
    assert len(results) == 2

    # First: regex path
    regex_stmt = results[0]
    assert regex_stmt.keyword_count == 1
    regex_param = regex_stmt.query_parameters[0]
    assert regex_param.value == "(?i)f[o0]+bar"

    # Second: standard path (2 keywords)
    standard_stmt = results[1]
    assert standard_stmt.keyword_count == 2


def test_build_class_select_statements_no_is_regex_key_defaults_to_standard():
    """Test backwards compat: configs without is_regex key use the standard path."""
    class_configs: list[keyword_match_schemas.ClassToKeywordConfig] = [
        {"class_name": "old_config", "musts": "hello world"},
    ]
    results = kms._build_class_select_statements(class_configs)
    assert len(results) == 1
    assert results[0].keyword_count == 2  # two keywords, not one


def test_build_class_select_statements_is_regex_with_nots():
    """Test is_regex=True with nots treated as a raw RE2 regex."""
    class_configs: list[keyword_match_schemas.ClassToKeywordConfig] = [
        {
            "class_name": "hate_speech",
            "musts": "(?i)[g9][e3]nd[e3]r",
            "nots": "(?i)neutral",
            "is_regex": True,
        },
    ]
    results = kms._build_class_select_statements(class_configs)
    assert len(results) == 1
    stmt = results[0]
    # 1 musts regex + 1 nots regex
    assert stmt.keyword_count == 2
    # params: musts regex, nots regex, class_name
    assert len(stmt.query_parameters) == 3
    assert stmt.query_parameters[1].value == "(?i)neutral"
    assert "NOT REGEXP_CONTAINS" in stmt.select_statement


def test_build_class_select_statements_standard_with_nots():
    """Test standard mode with nots tokenized and negated."""
    class_configs: list[keyword_match_schemas.ClassToKeywordConfig] = [
        {
            "class_name": "fruit",
            "musts": "apples",
            "nots": "rotten bad",
        },
    ]
    results = kms._build_class_select_statements(class_configs)
    assert len(results) == 1
    stmt = results[0]
    # 1 must keyword + 2 not keywords
    assert stmt.keyword_count == 3
    assert "NOT REGEXP_CONTAINS" in stmt.select_statement


def test_build_class_select_statements_empty_nots_ignored():
    """Test that empty nots string produces no NOT conditions."""
    class_configs: list[keyword_match_schemas.ClassToKeywordConfig] = [
        {
            "class_name": "test",
            "musts": "hello",
            "nots": "",
        },
    ]
    results = kms._build_class_select_statements(class_configs)
    assert len(results) == 1
    stmt = results[0]
    assert stmt.keyword_count == 1
    assert "NOT REGEXP_CONTAINS" not in stmt.select_statement


def _make_class_statement(keyword_count: int) -> kms.ClassSelectStatement:
    """Helper to create a ClassSelectStatement with a given keyword count."""
    return kms.ClassSelectStatement(
        select_statement="SELECT ...",
        query_parameters=[],
        keyword_count=keyword_count,
    )


@pytest.mark.parametrize(
    "keyword_counts,keywords_per_batch,expected_batch_keyword_counts",
    [
        # Empty list -> no batches
        ([], 100, []),
        # Single statement fits in one batch
        ([5], 100, [[5]]),
        # Single statement exceeds batch size but still goes in one batch
        # (we don't split a single class across batches)
        ([150], 100, [[150]]),
        # Two statements that fit in one batch
        ([30, 40], 100, [[30, 40]]),
        # Two statements that don't fit together
        ([60, 60], 100, [[60], [60]]),
        # Three statements: first two fit, third starts new batch
        ([40, 40, 40], 100, [[40, 40], [40]]),
        # Exact fit at boundary
        ([50, 50], 100, [[50, 50]]),
        # Just over boundary
        ([50, 51], 100, [[50], [51]]),
        # Multiple batches with varying sizes
        ([10, 20, 30, 40, 50], 100, [[10, 20, 30, 40], [50]]),
        # Each statement exceeds limit individually
        ([101, 102, 103], 100, [[101], [102], [103]]),
        # Mix of small and large
        ([10, 150, 20, 30], 100, [[10], [150], [20, 30]]),
    ],
)
def test_chunk_by_keyword_count(
    keyword_counts: list[int],
    keywords_per_batch: int,
    expected_batch_keyword_counts: list[list[int]],
):
    """Test that _chunk_by_keyword_count correctly groups statements by keyword count."""
    # Create ClassSelectStatements with the given keyword counts
    statements = [_make_class_statement(count) for count in keyword_counts]

    # Chunk them
    batches = kms._chunk_by_keyword_count(statements, keywords_per_batch)

    # Extract keyword counts from each batch for comparison
    actual_batch_keyword_counts = [[stmt.keyword_count for stmt in batch] for batch in batches]

    assert actual_batch_keyword_counts == expected_batch_keyword_counts
