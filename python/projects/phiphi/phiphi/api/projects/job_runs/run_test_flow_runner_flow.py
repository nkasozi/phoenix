"""Run a test flow_runner_flow.

See phiphi/docs/debugging_flows_locally.md for more information on how to set this up.

This is configured to use correct data from seeded data (what is in the platform db if you
do `make up`.)

Usage:
    python -m phiphi.api.projects.job_runs.run_test_flow_runner_flow
"""

import asyncio

from phiphi.api.projects.job_runs import flow_runner_flow, schemas

if __name__ == "__main__":
    asyncio.run(
        flow_runner_flow.flow_runner_flow(
            project_id=2,
            job_type=schemas.ForeignJobType.gather,
            job_source_id=3,
            job_run_id=6,
        )
    )
    # This is a gather classify tabulate run that can be used for testing.
    asyncio.run(
        flow_runner_flow.flow_runner_flow(
            project_id=6,
            job_type=schemas.ForeignJobType.gather_classify_tabulate,
            job_source_id=16,
            job_run_id=25,
        )
    )
