"""Routes for Hugging Face."""

import fastapi

from phiphi.api import deps
from phiphi.api.projects import deps as projects_deps
from phiphi.api.projects.classifiers.hugging_face import crud, model_validation, schemas

router = fastapi.APIRouter()


@router.post(
    "/projects/{project_id}/classifiers/hugging_face",
)
async def create_hugging_face_and_run(
    session: deps.SessionDep,
    project: projects_deps.ProjectUseAccessDep,
    classifier_create: schemas.HuggingFaceClassifierCreate,
) -> schemas.HuggingFaceClassifierDetail:
    """Create and run a new Hugging Face classifier."""
    model_id = classifier_create.latest_version.params.model_id
    # Validate the model ID against Hugging Face standards
    # With raise error if the model is not valid
    model_validation.is_valid_model(model_id)
    return await crud.create_classifier_and_run(
        session=session,
        project_id=project.id,
        classifier_create=classifier_create,
    )
