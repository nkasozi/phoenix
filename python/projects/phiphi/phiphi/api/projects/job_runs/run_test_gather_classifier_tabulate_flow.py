"""Run a test flow_runner_flow.

See phiphi/docs/debugging_flows_locally.md for more information on how to set this up.

This is configured to use correct data from seeded data (what is in the platform db if you
do `make up`.)

Usage:
    python -m phiphi.api.projects.job_runs.run_test_gather_classifier_tabulate_flow

BEAWARE:
    - There has been cases where this script behaved differently from the actual flow in the
      cluster. For instance, invoke_hf_flow worked here but not in the cluster.
"""

import asyncio
import datetime

from phiphi.api.projects.classifiers import base_schemas, bucketing_schemas
from phiphi.api.projects.classifiers.hugging_face import schemas as hf_schemas
from phiphi.api.projects.gathers import schemas as gathers_schemas
from phiphi.api.projects.gathers.apify_x_advanced_searches_posts_comments import (
    schemas as x_gather_schemas,
)
from phiphi.pipeline_jobs.composite_flows import gather_classify_tabulate_flow

if __name__ == "__main__":
    # Create a gather using the ApifyXAdvancedSearchesPostsCommentsGatherResponse schema
    gather = x_gather_schemas.ApifyXAdvancedSearchesPostsCommentsGatherResponse(
        id=1,
        name="Test X Advanced Search Gather",
        project_id=6,
        child_type=gathers_schemas.ChildTypeName.apify_x_advanced_searches_posts_comments,
        created_at=datetime.datetime.fromisoformat("2025-10-31T14:03:38.791666"),
        updated_at=datetime.datetime.fromisoformat("2025-10-31T14:03:38.791671"),
        search_list=["from:NASA", "from:SpaceX"],
        limit_results_per_search=100,
        posts_created_after="2025-01-01",
        posts_created_before=None,
        sort="Latest",
    )
    gather_dict = gather.model_dump()

    # Create a classifier using HuggingFaceClassifierResponse schema
    classifier = hf_schemas.HuggingFaceClassifierResponse(
        id=16,
        name="Test HF",
        type=base_schemas.ClassifierType.hugging_face,
        project_id=1,
        description="",
        latest_version=hf_schemas.HuggingFaceVersionResponse(
            version_id=13,
            classifier_id=16,
            params=hf_schemas.HuggingFaceParams(
                model_id="distilbert-base-uncased-finetuned-sst-2-english",
                bucketing_configs=[
                    bucketing_schemas.BucketingConfig(
                        class_name="*",
                        buckets=[
                            bucketing_schemas.BucketThreshold(
                                name="low_prob", upper_threshold=0.25
                            ),
                            bucketing_schemas.BucketThreshold(
                                name="medium_prob", upper_threshold=0.5
                            ),
                            bucketing_schemas.BucketThreshold(
                                name="high_prob", upper_threshold=0.75
                            ),
                            bucketing_schemas.BucketThreshold(
                                name="very_high_prob", upper_threshold=1.0
                            ),
                        ],
                    )
                ],
            ),
            created_at=datetime.datetime.fromisoformat("2025-10-31T14:03:38.791666"),
            updated_at=datetime.datetime.fromisoformat("2025-10-31T14:03:38.791671"),
        ),
    )
    classifier_dict = classifier.model_dump()

    asyncio.run(
        gather_classify_tabulate_flow.gather_classify_tabulate_flow(
            project_id=6,
            project_namespace="project_id6",
            job_source_id=16,
            job_run_id=25,
            gather_dict=gather_dict,
            gather_child_type=gather.child_type,
            classifiers_dict_list=[classifier_dict],
            active_classifiers_versions=[(16, 13)],
        )
    )
