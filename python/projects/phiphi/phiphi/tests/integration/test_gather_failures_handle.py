"""Testing failures in the gathers are handled correctly."""

import datetime
from unittest import mock

import pytest

from phiphi import config
from phiphi.api.projects import gathers
from phiphi.pipeline_jobs.composite_flows import gather_classify_tabulate_flow


@pytest.mark.asyncio
@mock.patch("phiphi.pipeline_jobs.gathers.utils.load_sample_raw_data")
async def test_gather_account_not_available(m_load_sample_raw_data, tmp_bq_project):
    """Test gather data when the facebook account is not_available.

    The pipeline should be sucessfull even if there is only failures in the scraped data.
    """
    if config.settings.USE_MOCK_BQ:
        raise Exception(
            "This test requires USE_MOCK_BQ to be set to False. "
            "Please change this in python/projects/phiphi/docker_env.dev."
        )

    test_project_namespace = tmp_bq_project

    batch_size = 20

    mock_scraped_data = [
        {
            "url": "https://www.facebook.com/someaccountthatdoesnotexistjkdljslfk",
            "error": "not_available",
            "errorDescription": (
                "This content isn't available because the owner only shared it with a small group "
                "of people or changed who can see it, or it's been deleted."
            ),
        }
    ]

    m_load_sample_raw_data.return_value = mock_scraped_data

    gather = gathers.apify_facebook_posts.schemas.ApifyFacebookPostsGatherResponse(
        name="Example",
        limit_posts_per_account=4,
        account_url_list=[
            "https://www.facebook.com/someaccountthatdoesnotexistjkdljslfk",
        ],
        posts_created_after="2018-12-01",
        posts_created_before="2018-12-30",
        id=1,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        project_id=1,
        latest_job_run=None,
        child_type=gathers.schemas.ChildTypeName.apify_facebook_posts,
    )
    # Currently this throws an error due to the generalised_messages not being created.
    result = await gather_classify_tabulate_flow.gather_classify_tabulate_flow(
        project_id=1,
        job_source_id=1,
        job_run_id=1,
        project_namespace=test_project_namespace,
        gather_dict=gather.dict(),
        gather_child_type=gather.child_type,
        classifiers_dict_list=[],
        active_classifiers_versions=[],
        max_mb_batch_size=batch_size,
    )
    assert result.gather_job_result is not None
    assert result.gather_job_result.result_count == 1
