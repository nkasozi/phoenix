"""Main for phiphi seed.

This module is used to seed the database with initial data.

Usage (from the projects/phiphi/):
    python phiphi/seed/main.py
"""

import argparse
import logging

from sqlalchemy.orm import Session

from phiphi import (
    # This is needed for the drop all tables to work
    all_platform_models,  # noqa: F401
    platform_db,
    utils,
)
from phiphi.seed import (
    apify_facebook_comments_gather,
    apify_facebook_posts_gather,
    apify_facebook_search_posts_gather,
    apify_tiktok_accounts_posts_gather,
    apify_tiktok_comments_gather,
    apify_tiktok_hashtags_posts_gather,
    apify_tiktok_searches_posts_gather,
    apify_x_advanced_searches_posts_comments_gather,
    apify_x_simple_searches_posts_comments_gather,
    classifiers,
    credit_allocations,
    danek_facebook_searches_posts_gather,
    danek_instagram_comments_gather,
    danek_instagram_posts_gather,
    job_runs,
    projects,
    user_project_associations,
    users,
    workspaces,
)

utils.init_logging()
utils.init_sentry()

main_logger = logging.getLogger(__name__)


def main(session: Session, testing: bool = False) -> None:
    """Seed the database.

    If testing is true the databased will be dropped and recreated.
    """
    if testing:
        platform_db.Base.metadata.drop_all(
            bind=session.get_bind()
        )  # Drop all tables if --testing flag is provided
        platform_db.Base.metadata.create_all(session.get_bind())  # Create all tables again
    users.init_first_admin_user(session)
    workspaces.init_main_workspace(session)

    if testing:
        users.seed_test_users(session)
        workspaces.seed_test_workspace(session)
        projects.seed_test_project(session)
        apify_facebook_posts_gather.seed_test_apify_facebook_posts_gathers(session)
        apify_facebook_comments_gather.seed_test_apify_facebook_comments_gathers(session)
        apify_tiktok_accounts_posts_gather.seed_test_apify_tiktok_accounts_posts_gathers(session)
        apify_tiktok_hashtags_posts_gather.seed_test_apify_tiktok_hashtags_posts_gathers(session)
        apify_tiktok_searches_posts_gather.seed_test_apify_tiktok_searches_posts_gathers(session)
        apify_tiktok_comments_gather.seed_test_apify_tiktok_comments_gathers(session)
        apify_x_advanced_searches_posts_comments_gather.seed_test_apify_x_advanced_searches_posts_comments_gathers(
            session
        )
        apify_x_simple_searches_posts_comments_gather.seed_test_apify_x_simple_searches_posts_comments_gathers(
            session
        )
        apify_facebook_search_posts_gather.seed_test_apify_facebook_search_posts_gathers(session)
        danek_facebook_searches_posts_gather.seed_test_danek_facebook_searches_posts_gathers(
            session
        )
        danek_instagram_posts_gather.seed_test_danek_instagram_posts_gathers(session)
        danek_instagram_comments_gather.seed_test_danek_instagram_comments_gathers(session)
        job_runs.seed_test_job_runs(session)
        classifiers.keyword_match_seed.seed_test_classifier_keyword_match(session)
        classifiers.manual_post_authors_seed.seed_test_classifiers_manual_post_authors(session)
        classifiers.perspective_api_seed.seed_test_classifiers_perspective_api(session)
        user_project_associations.seed_test_user_project_associations(session)
        credit_allocations.seed_test_credit_allocations(session)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the database", prog="main")
    parser.add_argument(
        "--testing", action="store_true", help="Drop and recreate the database for testing"
    )
    args = parser.parse_args()

    if args.testing:
        main_logger.info("Seeding the database --testing")
    else:
        main_logger.info("Seeding the database")
    with Session(platform_db.engine) as session:
        main(session, args.testing)
    main_logger.info("Finished seeding the database")
