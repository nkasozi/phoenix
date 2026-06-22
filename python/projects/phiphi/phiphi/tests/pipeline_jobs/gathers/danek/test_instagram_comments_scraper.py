"""Test Instagram Comments Scraper."""

from typing import Any, List, Tuple
from unittest import mock

from phiphi.pipeline_jobs.gathers.danek.instagram_comments_scraper import (
    collect_child_comments_from_raw_json,
)


@mock.patch(
    "phiphi.pipeline_jobs.gathers.danek.instagram_comments_scraper.normalise.prepare_batch_json_for_normalisation"
)
def test_collect_child_comments_single_match(mock_prepare):
    """Test that a single comment with child comments is collected.

    Args:
        mock_prepare: Mocked normaliser function.
    """
    collected: List[Tuple[str, str]] = []
    payload = {"post_id": "post123"}

    mock_prepare.return_value = (
        [{"pk": "c1", "child_comment_count": 2}],
        [],
    )

    collect_child_comments_from_raw_json({}, payload, collected)

    assert collected == [("c1", "post123")]


@mock.patch(
    "phiphi.pipeline_jobs.gathers.danek.instagram_comments_scraper.normalise.prepare_batch_json_for_normalisation"
)
def test_collect_child_comments_no_children(mock_prepare):
    """Test that no comments are collected when child_comment_count is zero.

    Args:
        mock_prepare: Mocked normaliser function.
    """
    collected: List[Tuple[str, str]] = []
    payload = {"post_id": "post123"}

    mock_prepare.return_value = (
        [{"pk": "c1", "child_comment_count": 0}],
        [],
    )

    collect_child_comments_from_raw_json({}, payload, collected)

    assert collected == []


@mock.patch(
    "phiphi.pipeline_jobs.gathers.danek.instagram_comments_scraper.normalise.prepare_batch_json_for_normalisation"
)
def test_collect_child_comments_multiple_matches(mock_prepare):
    """Test that multiple comments with child comments are collected.

    Args:
        mock_prepare: Mocked normaliser function.
    """
    collected: List[Tuple[str, str]] = []
    payload = {"post_id": "post123"}

    mock_prepare.return_value = (
        [
            {"pk": "c1", "child_comment_count": 1},
            {"pk": "c2", "child_comment_count": 3},
            {"pk": "c3", "child_comment_count": 0},
        ],
        [],
    )

    collect_child_comments_from_raw_json({}, payload, collected)

    assert collected == [
        ("c1", "post123"),
        ("c2", "post123"),
    ]


@mock.patch(
    "phiphi.pipeline_jobs.gathers.danek.instagram_comments_scraper.normalise.prepare_batch_json_for_normalisation"
)
def test_collect_child_comments_missing_pk(mock_prepare):
    """Test that missing 'pk' results in no items.

    Args:
        mock_prepare: Mocked normaliser function.
    """
    collected: List[Tuple[str, str]] = []
    payload = {"post_id": "post123"}

    mock_prepare.return_value = (
        [{"child_comment_count": 2}],
        [],
    )

    collect_child_comments_from_raw_json({}, payload, collected)

    assert len(collected) == 0


@mock.patch(
    "phiphi.pipeline_jobs.gathers.danek.instagram_comments_scraper.normalise.prepare_batch_json_for_normalisation"
)
def test_collect_child_comments_missing_post_id(mock_prepare):
    """Test that missing post_id in payload results in no items.

    Args:
        mock_prepare: Mocked normaliser function.
    """
    collected: List[Tuple[str, str]] = []
    payload: dict[str, Any] = {}

    mock_prepare.return_value = (
        [{"pk": "c1", "child_comment_count": 1}],
        [],
    )

    collect_child_comments_from_raw_json({}, payload, collected)

    assert len(collected) == 0


@mock.patch(
    "phiphi.pipeline_jobs.gathers.danek.instagram_comments_scraper.normalise.prepare_batch_json_for_normalisation"
)
def test_collect_child_comments_calls_normaliser(mock_prepare):
    """Test that the normaliser is called exactly once.

    Args:
        mock_prepare: Mocked normaliser function.
    """
    collected: List[Tuple[str, str]] = []
    payload = {"post_id": "post123"}

    mock_prepare.return_value = ([], [])

    collect_child_comments_from_raw_json({}, payload, collected)

    mock_prepare.assert_called_once()
