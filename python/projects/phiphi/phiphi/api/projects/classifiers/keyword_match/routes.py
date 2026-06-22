"""Keyword Match routes."""

import fastapi
from fastapi.responses import StreamingResponse

from phiphi.api import deps
from phiphi.api.projects import classifiers
from phiphi.api.projects import deps as project_deps
from phiphi.api.projects.classifiers import base_schemas, response_schemas
from phiphi.api.projects.classifiers.keyword_match import crud, schemas

router = fastapi.APIRouter()


@router.post(
    "/projects/{project_id}/classifiers/keyword_match",
)
def create_keyword_match_classifier(
    session: deps.SessionDep,
    project: project_deps.ProjectUseAccessDep,
    classifier_create: base_schemas.ClassifierWithIntermediatoryCreate,
) -> response_schemas.ClassifierDetail:
    """Create a new keyword match classifier."""
    return classifiers.crud.create_classifier(
        session=session,
        project_id=project.id,
        classifier_type=base_schemas.ClassifierType.keyword_match,
        classifier_create=classifier_create,
    )


@router.post(
    "/projects/{project_id}/classifiers/keyword_match/{classifier_id}/version_and_run",
)
async def create_keyword_match_version_and_run(
    session: deps.SessionDep,
    project: project_deps.ProjectUseAccessDep,
    classifier_id: int,
) -> response_schemas.ClassifierDetail:
    """Create a new keyword match version and run."""
    return await crud.create_version_and_run(
        session=session,
        project_id=project.id,
        classifier_id=classifier_id,
    )


@router.post(
    "/projects/{project_id}/classifiers/keyword_match/{classifier_id}/import_csv",
)
def import_keyword_match_csv(
    session: deps.SessionDep,
    project: project_deps.ProjectUseAccessDep,
    classifier_id: int,
    import_mode: schemas.ImportMode,
    file: fastapi.UploadFile = fastapi.File(...),
) -> response_schemas.ClassifierDetail:
    """Import keyword match classifier configs from a CSV file."""
    return crud.import_keyword_configs_csv(
        session=session,
        project_id=project.id,
        classifier_id=classifier_id,
        file=file.file,
        import_mode=import_mode,
    )


@router.get(
    "/projects/{project_id}/classifiers/keyword_match/{classifier_id}/export_csv",
)
def export_keyword_match_csv(
    session: deps.SessionDep,
    project: project_deps.ProjectViewAccessDep,
    classifier_id: int,
) -> StreamingResponse:
    """Export keyword match classifier configs as CSV."""
    csv_string = crud.export_keyword_configs_csv(
        session=session,
        project_id=project.id,
        classifier_id=classifier_id,
    )
    filename = f"keyword_classifier_export_project_{project.id}_classifier_{classifier_id}.csv"
    return StreamingResponse(
        iter([csv_string]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post(
    "/projects/{project_id}/classifiers/keyword_match/{classifier_id}/intermediatory_class_to_keyword_configs",
)
def create_keyword_match_intermediatory_class_to_keyword_config(
    session: deps.SessionDep,
    project: project_deps.ProjectUseAccessDep,
    classifier_id: int,
    intermediatory_class_to_keyword_config: schemas.IntermediatoryClassToKeywordConfigCreate,
) -> schemas.IntermediatoryClassToKeywordConfigResponse:
    """Create an intermediatory class to keyword config."""
    return crud.create_intermediatory_class_to_keyword_config(
        session=session,
        project_id=project.id,
        classifier_id=classifier_id,
        intermediatory_class_to_keyword_config=intermediatory_class_to_keyword_config,
    )


@router.put(
    "/projects/{project_id}/classifiers/keyword_match/{classifier_id}/intermediatory_class_to_keyword_configs/{config_id}",
)
def put_keyword_match_intermediatory_class_to_keyword_config(
    session: deps.SessionDep,
    project: project_deps.ProjectUseAccessDep,
    classifier_id: int,
    config_id: int,
    intermediatory_class_to_keyword_config: schemas.IntermediatoryClassToKeywordConfigCreate,
) -> schemas.IntermediatoryClassToKeywordConfigResponse:
    """Put an intermediatory class to keyword config."""
    return crud.put_intermediatory_class_to_keyword_config(
        session=session,
        project_id=project.id,
        classifier_id=classifier_id,
        intermediatory_class_to_keyword_config_id=config_id,
        intermediatory_class_to_keyword_config=intermediatory_class_to_keyword_config,
    )


@router.delete(
    "/projects/{project_id}/classifiers/keyword_match/{classifier_id}/intermediatory_class_to_keyword_configs/{config_id}",
)
def delete_keyword_match_intermediatory_class_to_keyword_config(
    session: deps.SessionDep,
    project: project_deps.ProjectUseAccessDep,
    classifier_id: int,
    config_id: int,
) -> None:
    """Delete an intermediatory class to keyword config."""
    crud.delete_intermediatory_class_to_keyword_config(
        session=session,
        project_id=project.id,
        classifier_id=classifier_id,
        intermediatory_class_to_keyword_config_id=config_id,
    )
