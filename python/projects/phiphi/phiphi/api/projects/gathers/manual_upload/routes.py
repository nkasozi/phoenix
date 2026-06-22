"""Manual upload route."""

import fastapi

from phiphi.api import deps
from phiphi.api.projects import deps as projects_deps
from phiphi.api.projects.gathers.manual_upload import crud, file_processing, schemas

router = fastapi.APIRouter()


@router.post(
    "/projects/{project_id}/gathers/manual_upload/",
)
async def create_and_run_manual_upload_gather(
    session: deps.SessionDep,
    project: projects_deps.ProjectUseAccessDep,
    name: str = fastapi.Form(),
    file: fastapi.UploadFile = fastapi.File(...),
) -> schemas.ManualUploadGatherResponse:
    """Create and run a manual upload gather."""
    uploaded_file_meta_data = file_processing.process_manual_upload_file(
        file,
        project.id,
    )
    gather_response = await crud.create_and_run_manual_upload_gather(
        session=session,
        project_id=project.id,
        name=name,
        uploaded_file_meta_data=uploaded_file_meta_data,
    )
    return gather_response
