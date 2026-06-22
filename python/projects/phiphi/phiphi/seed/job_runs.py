"""Seed the Job runs.

We are using a very simple and brittle seeding of the database.

In that we have to check the ids of the projects and gathers in the database
to seed the correct job runs.

Currently this script will seed 3 job runs in the database. This includes a job run for all the
apify_facebook_gathers:
- 2 job runs in project 1
- 1 job run in project 2
"""

import datetime

from sqlalchemy.orm import Session

from phiphi.api.projects.gathers import crud as gather_crud
from phiphi.api.projects.job_runs import crud, schemas

TEST_JOB_RUN = schemas.JobRunCreate(
    foreign_id=1, foreign_job_type=schemas.ForeignJobType.gather_classify_tabulate
)

TEST_JOB_RUN_2 = schemas.JobRunCreate(foreign_id=2, foreign_job_type=schemas.ForeignJobType.gather)

TEST_JOB_RUN_3 = schemas.JobRunCreate(foreign_id=3, foreign_job_type=schemas.ForeignJobType.gather)
TEST_JOB_RUN_4 = schemas.JobRunCreate(
    foreign_id=0, foreign_job_type=schemas.ForeignJobType.tabulate
)

TEST_GATHER_DELETED_JOB_RUN = schemas.JobRunCreate(
    foreign_id=2, foreign_job_type=schemas.ForeignJobType.delete_gather
)

TEST_JOB_RUN_5 = schemas.JobRunCreate(
    foreign_id=2, foreign_job_type=schemas.ForeignJobType.gather_classify_tabulate
)

TEST_JOB_RUN_6 = schemas.JobRunCreate(
    foreign_id=7, foreign_job_type=schemas.ForeignJobType.gather_classify_tabulate
)

TEST_GATHER_FAILED_DELETED_GATHER_RUN = schemas.JobRunCreate(
    foreign_id=8, foreign_job_type=schemas.ForeignJobType.gather_classify_tabulate
)

TEST_GATHER_FAILED_DELETED_JOB_RUN = schemas.JobRunCreate(
    foreign_id=8, foreign_job_type=schemas.ForeignJobType.delete_gather
)

TEST_GATHER_RUNNING_DELETED_GATHER_RUN = schemas.JobRunCreate(
    foreign_id=9, foreign_job_type=schemas.ForeignJobType.gather_classify_tabulate
)

TEST_GATHER_RUNNING_DELETED_JOB_RUN = schemas.JobRunCreate(
    foreign_id=9, foreign_job_type=schemas.ForeignJobType.delete_gather
)


TEST_CLASSIFY_RUNNING_JOB_RUN = schemas.JobRunCreate(
    foreign_id=3, foreign_job_type=schemas.ForeignJobType.classify_tabulate
)

TEST_CLASSIFY_COMPLETED_JOB_RUN = schemas.JobRunCreate(
    foreign_id=4, foreign_job_type=schemas.ForeignJobType.classify_tabulate
)

TEST_CLASSIFY_FAILED_JOB_RUN = schemas.JobRunCreate(
    foreign_id=5, foreign_job_type=schemas.ForeignJobType.classify_tabulate
)

TEST_CLASSIFY_ARCHIVE_RUNNING_JOB_RUN = schemas.JobRunCreate(
    foreign_id=2, foreign_job_type=schemas.ForeignJobType.classifier_archive
)

TEST_CLASSIFY_ARCHIVE_COMPLETED_JOB_RUN = schemas.JobRunCreate(
    foreign_id=6, foreign_job_type=schemas.ForeignJobType.classifier_archive
)

TEST_CLASSIFY_ARCHIVE_FAILED_JOB_RUN = schemas.JobRunCreate(
    foreign_id=7, foreign_job_type=schemas.ForeignJobType.classifier_archive
)

TEST_CLASSIFY_RESTORE_RUNNING_JOB_RUN = schemas.JobRunCreate(
    foreign_id=8, foreign_job_type=schemas.ForeignJobType.classifier_restore
)

TEST_CLASSIFY_RESTORE_COMPLETED_JOB_RUN = schemas.JobRunCreate(
    foreign_id=9, foreign_job_type=schemas.ForeignJobType.classifier_restore
)

TEST_CLASSIFY_RESTORE_FAILED_JOB_RUN = schemas.JobRunCreate(
    foreign_id=10, foreign_job_type=schemas.ForeignJobType.classifier_restore
)

TEST_CLASSIFY_COMPLETED_JOB_RUN_2 = schemas.JobRunCreate(
    foreign_id=11, foreign_job_type=schemas.ForeignJobType.classify_tabulate
)

# This is the job run for project 3 that has cost to match the allocated credits
TEST_GATHER_COMPLETED_JOB_RUN_PROJECT_3_WITH_COSTS = schemas.JobRunCreate(
    foreign_id=13, foreign_job_type=schemas.ForeignJobType.gather_classify_tabulate
)

# These are the job runs for project 6 that have estimated costs greater than the allocated credits
TEST_GATHER_COMPLETED_JOB_RUN_PROJECT_6_WITH_ESTIMATED_COSTS_1 = schemas.JobRunCreate(
    foreign_id=15,
    foreign_job_type=schemas.ForeignJobType.gather_classify_tabulate,
    # Making the estimated_total_cost different between the two job runs in the project so we know
    # the correct job run is being used in the calculation of the projects estimated_total_costs
    estimated_total_cost=99,
)

TEST_GATHER_COMPLETED_JOB_RUN_PROJECT_6_WITH_ESTIMATED_COSTS_1_TOTAL_COST = 50

TEST_GATHER_RUNNING_JOB_RUN_PROJECT_6_WITH_ESTIMATED_COSTS_2 = schemas.JobRunCreate(
    foreign_id=16,
    foreign_job_type=schemas.ForeignJobType.gather_classify_tabulate,
    estimated_total_cost=100,
)

SEEDED_JOB_RUNS: list[schemas.JobRunResponse] = []


def create_deleted_job_run(
    session: Session,
    project_id: int,
    job_run_create: schemas.JobRunCreate,
    status: schemas.Status | None = schemas.Status.completed_successfully,
) -> None:
    """Create a deleted job run."""
    job_run_response = crud.create_job_run(
        session=session, project_id=project_id, job_run_create=job_run_create
    )
    if status:
        crud.update_job_run(
            session=session,
            job_run_data=schemas.JobRunUpdateCompleted(
                id=job_run_response.id,
                # Making the completed at related to the id of the job run
                completed_at=job_run_response.created_at
                + datetime.timedelta(seconds=job_run_response.id),
                status=status,
            ),
        )
    gather_db = gather_crud.get_orm_gather(
        session=session, project_id=project_id, gather_id=job_run_create.foreign_id
    )
    if gather_db is None:
        raise ValueError("Gather not found")
    gather_db.delete_job_run_id = job_run_response.id
    session.commit()


def create_job_run_and_complete(
    session: Session,
    project_id: int,
    job_run_create: schemas.JobRunCreate,
    status: schemas.Status = schemas.Status.completed_successfully,
    total_costs: float | None = None,
    gather_result_count: int = 1,
    gather_normalise_error_count: int = 0,
    is_total_cost_estimated: bool = False,
) -> schemas.JobRunResponse:
    """Create a job run and complete it."""
    job_run_response = crud.create_job_run(
        session=session, project_id=project_id, job_run_create=job_run_create
    )
    return crud.update_job_run(
        session=session,
        job_run_data=schemas.JobRunUpdateCompleted(
            id=job_run_response.id,
            # Making the completed at related to the id of the job run
            completed_at=job_run_response.created_at
            + datetime.timedelta(seconds=job_run_response.id),
            status=status,
            total_cost=total_costs,
            gather_result_count=gather_result_count,
            gather_normalise_error_count=gather_normalise_error_count,
            is_total_cost_estimated=is_total_cost_estimated,
        ),
    )


def seed_test_job_runs(session: Session) -> None:
    """Seed the job runs."""
    SEEDED_JOB_RUNS.clear()
    job_runs_project_1 = [
        TEST_JOB_RUN,
        TEST_JOB_RUN_2,
        TEST_JOB_RUN_4,
        TEST_JOB_RUN_5,
    ]

    for job_run in job_runs_project_1:
        job_run_response = create_job_run_and_complete(session, 1, job_run)
        SEEDED_JOB_RUNS.append(job_run_response)

    # Create a second gather run for gather 1
    # This is in status awaiting_start
    SEEDED_JOB_RUNS.append(
        crud.create_job_run(session=session, project_id=1, job_run_create=TEST_JOB_RUN)
    )

    # This needs to be the only job in project 2 other wise we can't check that
    # `last_job_run_completed_at` is None for project 2
    SEEDED_JOB_RUNS.append(
        crud.create_job_run(session=session, project_id=2, job_run_create=TEST_JOB_RUN_3)
    )

    # Deleted job for gather
    create_deleted_job_run(session, 1, TEST_GATHER_DELETED_JOB_RUN)

    # Create a second gather run for gather 7 so we have a completed gather that is not deleted
    create_job_run_and_complete(session, 1, TEST_JOB_RUN_6)

    # Make gather id 5 completed gather and have a failed deleted gather run
    create_job_run_and_complete(session, 1, TEST_GATHER_FAILED_DELETED_GATHER_RUN)
    create_deleted_job_run(session, 1, TEST_GATHER_FAILED_DELETED_JOB_RUN, schemas.Status.failed)

    # Make gather id 9 completed gather and have a running deleted gather run
    create_job_run_and_complete(session, 1, TEST_GATHER_RUNNING_DELETED_GATHER_RUN)
    create_deleted_job_run(session, 1, TEST_GATHER_RUNNING_DELETED_JOB_RUN, None)
    # Classify
    create_job_run_and_complete(session, 1, TEST_CLASSIFY_COMPLETED_JOB_RUN)
    create_job_run_and_complete(session, 1, TEST_CLASSIFY_FAILED_JOB_RUN, schemas.Status.failed)
    crud.create_job_run(session, 1, TEST_CLASSIFY_RUNNING_JOB_RUN)

    create_job_run_and_complete(session, 1, TEST_CLASSIFY_ARCHIVE_COMPLETED_JOB_RUN)
    create_job_run_and_complete(
        session, 1, TEST_CLASSIFY_ARCHIVE_FAILED_JOB_RUN, schemas.Status.failed
    )
    crud.create_job_run(session, 1, TEST_CLASSIFY_ARCHIVE_RUNNING_JOB_RUN)

    create_job_run_and_complete(session, 1, TEST_CLASSIFY_RESTORE_COMPLETED_JOB_RUN)
    create_job_run_and_complete(
        session, 1, TEST_CLASSIFY_RESTORE_FAILED_JOB_RUN, schemas.Status.failed
    )
    create_job_run_and_complete(
        session, 3, TEST_GATHER_COMPLETED_JOB_RUN_PROJECT_3_WITH_COSTS, total_costs=100
    )

    # Project 1 jobs to check last_job_run_completed_at
    create_job_run_and_complete(session, 1, TEST_CLASSIFY_COMPLETED_JOB_RUN_2)
    crud.create_job_run(session, 1, TEST_CLASSIFY_RESTORE_RUNNING_JOB_RUN)
    # !!!!!!!!!!!!!!!!!!!!!
    # The last job run in project 1 needs to not be complete
    # !!!!!!!!!!!!!!!!!!!!!

    # Project 6 job runs
    create_job_run_and_complete(
        session,
        6,
        TEST_GATHER_COMPLETED_JOB_RUN_PROJECT_6_WITH_ESTIMATED_COSTS_1,
        total_costs=TEST_GATHER_COMPLETED_JOB_RUN_PROJECT_6_WITH_ESTIMATED_COSTS_1_TOTAL_COST,
        gather_normalise_error_count=10,
        is_total_cost_estimated=True,
    )
    crud.create_job_run(session, 6, TEST_GATHER_RUNNING_JOB_RUN_PROJECT_6_WITH_ESTIMATED_COSTS_2)
