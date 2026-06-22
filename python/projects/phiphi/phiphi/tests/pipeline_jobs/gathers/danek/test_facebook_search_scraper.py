"""Test facebook search scraper."""

import datetime
from unittest import mock

from phiphi.api.projects import gathers
from phiphi.pipeline_jobs import dataframe_writers
from phiphi.pipeline_jobs.gathers import gather_batch_write_managers
from phiphi.pipeline_jobs.gathers.danek import facebook_search_scraper


@mock.patch("phiphi.utils.get_danek_api_token")
def test_full_gather_scrape(
    mock_get_danek_api_token, danek_facebook_searches_posts_gather_fixture, requests_mock
):
    """Test full gather get."""
    mock_get_danek_api_token.return_value = "token"
    results = [{"data": "data"}] * 5
    data = {
        "results": results,
        "cursor": None,
    }
    requests_mock.post(facebook_search_scraper.DEFAULT_URL, json=data)
    gather = danek_facebook_searches_posts_gather_fixture
    proxy_code_enum = gathers.danek_facebook_searches_posts.schemas.ProxyCodes
    gather.proxy_country_to_gather_from = proxy_code_enum.US
    gather.recent_posts = True
    write_manager = gather_batch_write_managers.GatherBatchWriteManager(
        static_data=gather_batch_write_managers.GatherBatchStaticData(
            gather_id=1,
            job_run_id=1,
            gather_type=gather.child_type,
        ),
        df_writer=dataframe_writers.DummyWriter(),
    )
    facebook_search_scraper.scrape_facebook_searches_and_add_to_write_manager(
        gather=gather,
        write_manager=write_manager,
    )
    assert write_manager.complete_write().total_items_processed == 10
    # Assert that the POST request was made with the correct parameters
    assert len(requests_mock.request_history) == 2
    request = requests_mock.request_history[0]

    # Assert the URL
    assert request.url == facebook_search_scraper.DEFAULT_URL

    # Assert the headers
    expected_headers = {
        "Authorization": "Bearer token",
        "Content-Type": "application/json",
    }
    for key, value in expected_headers.items():
        assert request.headers[key] == value

    # Assert the JSON body
    expected_json = {
        "query": gather.search_list[0],
        "search_type": "POSTS_TAB",
        "search_config": {
            "start_date": gather.posts_created_after,
            "end_date": gather.posts_created_before,
            "recent_posts": gather.recent_posts,
            "proxy_code": "us",
        },
        "cursor": None,
    }
    assert request.json() == expected_json

    request = requests_mock.request_history[1]

    # Assert the URL
    assert request.url == facebook_search_scraper.DEFAULT_URL

    # Assert the headers
    expected_headers = {
        "Authorization": "Bearer token",
        "Content-Type": "application/json",
    }
    for key, value in expected_headers.items():
        assert request.headers[key] == value

    # Assert the JSON body for the second search query
    expected_json = {
        "query": gather.search_list[1],
        "search_type": "POSTS_TAB",
        "search_config": {
            "start_date": gather.posts_created_after,
            "end_date": gather.posts_created_before,
            "recent_posts": gather.recent_posts,
            "proxy_code": "us",
        },
        "cursor": None,
    }
    assert request.json() == expected_json


@mock.patch("phiphi.utils.get_danek_api_token")
def test_minimal_scrape(
    mock_get_danek_api_token,
    requests_mock,
):
    """Test minimal scrape."""
    mock_get_danek_api_token.return_value = "token"
    results = [{"data": "data"}] * 5
    data = {
        "results": results,
        "cursor": None,
    }
    gather = (
        gathers.danek_facebook_searches_posts.schemas.DanekFacebookSearchesPostsGatherResponse(
            name="Example",
            id=8,
            project_id=1,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
            latest_job_run=None,
            child_type=gathers.schemas.ChildTypeName.danek_facebook_searches_posts,
            search_list=["tech innovation"],
            stop_scraping_per_search_after_count=20,
            recent_posts=False,
        )
    )
    requests_mock.post(facebook_search_scraper.DEFAULT_URL, json=data)
    write_manager = gather_batch_write_managers.GatherBatchWriteManager(
        static_data=gather_batch_write_managers.GatherBatchStaticData(
            gather_id=1,
            job_run_id=1,
            gather_type=gather.child_type,
        ),
        df_writer=dataframe_writers.DummyWriter(),
    )
    facebook_search_scraper.scrape_facebook_searches_and_add_to_write_manager(
        gather=gather,
        write_manager=write_manager,
    )
    assert write_manager.complete_write().total_items_processed == 5
    # Assert that the POST request was made with the correct parameters
    assert len(requests_mock.request_history) == 1
    request = requests_mock.request_history[0]

    # Assert the URL
    assert request.url == facebook_search_scraper.DEFAULT_URL

    # Assert the headers
    expected_headers = {
        "Authorization": "Bearer token",
        "Content-Type": "application/json",
    }
    for key, value in expected_headers.items():
        assert request.headers[key] == value

    # Assert the JSON body
    expected_json = {
        "query": gather.search_list[0],
        "search_type": "POSTS_TAB",
        "search_config": {
            # Recent posts should always be added
            "recent_posts": gather.recent_posts,
        },
        "cursor": None,
    }
    assert request.json() == expected_json
