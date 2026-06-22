"""Crud for manual_upload."""

import sqlalchemy as sa

from phiphi.api.projects.gathers import crud as gather_crud
from phiphi.api.projects.gathers.manual_upload import file_processing, models, schemas
from phiphi.api.projects.job_runs import crud as job_run_crud
from phiphi.api.projects.job_runs import schemas as job_run_schemas


def create_manual_upload_gather(
    session: sa.orm.Session,
    project_id: int,
    name: str,
    uploaded_file_meta_data: file_processing.UploadedFileMetadata,
) -> schemas.ManualUploadGatherResponse:
    """Create a manual upload gather."""
    orm_gather = models.ManualUploadGather(
        project_id=project_id,
        name=name,
        uploaded_file_name=uploaded_file_meta_data.file_name_submited,
        file_url=uploaded_file_meta_data.file_url,
        file_size=uploaded_file_meta_data.file_size,
        file_row_count=uploaded_file_meta_data.file_row_count,
    )
    session.add(orm_gather)
    session.commit()
    session.refresh(orm_gather)
    return schemas.ManualUploadGatherResponse.model_validate(orm_gather)


async def create_and_run_manual_upload_gather(
    session: sa.orm.Session,
    project_id: int,
    name: str,
    uploaded_file_meta_data: file_processing.UploadedFileMetadata,
) -> schemas.ManualUploadGatherResponse:
    """Create and run a manual upload gather."""
    gather = create_manual_upload_gather(
        session=session,
        project_id=project_id,
        name=name,
        uploaded_file_meta_data=uploaded_file_meta_data,
    )
    _ = await job_run_crud.create_and_run_job_run(
        session,
        project_id,
        job_run_schemas.JobRunCreate(
            foreign_id=gather.id,
            foreign_job_type=job_run_schemas.ForeignJobType.gather_classify_tabulate,
            estimated_total_cost=gather.job_run_resource_estimate.max_total_cost,
        ),
    )

    orm_gather = gather_crud.get_orm_gather(session, project_id, gather.id)
    return schemas.ManualUploadGatherResponse.model_validate(orm_gather)
