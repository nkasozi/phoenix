"""Crud for keyword_match."""

import csv
import io
from typing import BinaryIO

import sqlalchemy as sa

from phiphi.api import exceptions
from phiphi.api.projects.classifiers import base_schemas as classifiers_base_schemas
from phiphi.api.projects.classifiers import crud
from phiphi.api.projects.classifiers import models as classifiers_models
from phiphi.api.projects.classifiers.keyword_match import models, schemas
from phiphi.api.projects.job_runs import crud as job_run_crud
from phiphi.api.projects.job_runs import schemas as job_run_schemas

CSV_HEADERS = ["class_name", "class_description", "musts", "nots", "is_regex"]
REQUIRED_CSV_COLUMNS = {"class_name", "class_description"}

UNIQUE_ERROR_MESSAGE = "The class to keyword match configuration already exists."
NOT_FOUND_ERROR_MESSAGE = "The class to keyword match configuration does not exist."


def create_version(
    session: sa.orm.Session,
    project_id: int,
    classifier_id: int,
) -> schemas.KeywordMatchVersionResponse:
    """Create a keyword match version."""
    orm_classifier = crud.get_orm_classifier(session, project_id, classifier_id)
    if orm_classifier is None:
        raise exceptions.ClassifierNotFound()

    if orm_classifier.type != classifiers_base_schemas.ClassifierType.keyword_match:
        raise exceptions.HttpException400("The classifier is not a keyword match classifier.")

    classes = crud.get_classes(session, orm_classifier)
    params = get_keyword_match_params(session, orm_classifier)

    orm_version = classifiers_models.ClassifierVersions(
        classifier_id=orm_classifier.id,
        classes=[class_label.model_dump() for class_label in classes],
        params=params,
    )
    session.add(orm_version)
    session.commit()
    session.refresh(orm_version)
    return schemas.KeywordMatchVersionResponse.model_validate(orm_version)


def get_keyword_match_params(
    session: sa.orm.Session,
    orm_classifier: classifiers_models.Classifiers,
) -> schemas.KeywordMatchParams:
    """Get keyword match params."""
    all_configs = orm_classifier.intermediatory_class_to_keyword_configs
    class_to_keyword_configs = []
    for orm_intermediatory_class_to_keyword_config in all_configs:
        class_to_keyword_config = schemas.ClassToKeywordConfig(
            class_name=orm_intermediatory_class_to_keyword_config.class_name,
            musts=orm_intermediatory_class_to_keyword_config.musts,
            nots=orm_intermediatory_class_to_keyword_config.nots,
            is_regex=orm_intermediatory_class_to_keyword_config.is_regex,
        )
        class_to_keyword_configs.append(class_to_keyword_config)
    return schemas.KeywordMatchParams(class_to_keyword_configs=class_to_keyword_configs)


async def create_version_and_run(
    session: sa.orm.Session,
    project_id: int,
    classifier_id: int,
) -> schemas.KeywordMatchClassifierDetail:
    """Create a keyword match version and run."""
    orm_classifier = crud.get_orm_classifier(session, project_id, classifier_id)
    if orm_classifier is None:
        raise exceptions.ClassifierNotFound()
    _ = create_version(session, project_id, classifier_id)
    _ = await job_run_crud.create_and_run_job_run(
        session,
        project_id,
        job_run_schemas.JobRunCreate(
            foreign_id=orm_classifier.id,
            foreign_job_type=job_run_schemas.ForeignJobType.classify_tabulate,
        ),
    )
    session.refresh(orm_classifier)
    return schemas.KeywordMatchClassifierDetail.model_validate(obj=orm_classifier)


def create_intermediatory_class_to_keyword_config(
    session: sa.orm.Session,
    project_id: int,
    classifier_id: int,
    intermediatory_class_to_keyword_config: schemas.IntermediatoryClassToKeywordConfigCreate,
) -> schemas.IntermediatoryClassToKeywordConfigResponse:
    """Create an intermediatory class to keyword config."""
    with crud.get_orm_classifier_with_edited_context(
        session, project_id, classifier_id
    ) as orm_classifier:
        try:
            # Attempt to add an object that may violate the unique constraint
            orm_intermediatory_class_to_keyword_config = models.IntermediatoryClassToKeywordConfig(
                classifier_id=orm_classifier.id,
                class_id=intermediatory_class_to_keyword_config.class_id,
                musts=intermediatory_class_to_keyword_config.musts,
                nots=intermediatory_class_to_keyword_config.nots,
                is_regex=intermediatory_class_to_keyword_config.is_regex,
            )
            session.add(orm_intermediatory_class_to_keyword_config)
            session.commit()
        except sa.exc.IntegrityError as e:
            session.rollback()
            if "unique constraint" in str(e):
                raise exceptions.HttpException400(UNIQUE_ERROR_MESSAGE)
            raise exceptions.UnknownIntegrityError()

    session.refresh(orm_intermediatory_class_to_keyword_config)
    return schemas.IntermediatoryClassToKeywordConfigResponse.model_validate(
        orm_intermediatory_class_to_keyword_config
    )


def put_intermediatory_class_to_keyword_config(
    session: sa.orm.Session,
    project_id: int,
    classifier_id: int,
    intermediatory_class_to_keyword_config_id: int,
    intermediatory_class_to_keyword_config: schemas.IntermediatoryClassToKeywordConfigCreate,
) -> schemas.IntermediatoryClassToKeywordConfigResponse:
    """Put an intermediatory class to keyword config."""
    with crud.get_orm_classifier_with_edited_context(
        session, project_id, classifier_id
    ) as orm_classifier:
        orm_intermediatory_class_to_keyword_config = (
            session.query(models.IntermediatoryClassToKeywordConfig)
            .filter(
                models.IntermediatoryClassToKeywordConfig.id
                == intermediatory_class_to_keyword_config_id,
                models.IntermediatoryClassToKeywordConfig.classifier_id == orm_classifier.id,
            )
            .one_or_none()
        )
        if orm_intermediatory_class_to_keyword_config is None:
            raise exceptions.HttpException404(NOT_FOUND_ERROR_MESSAGE)

        try:
            for key, value in intermediatory_class_to_keyword_config.model_dump(
                exclude_unset=True
            ).items():
                setattr(orm_intermediatory_class_to_keyword_config, key, value)

            session.commit()
        except sa.exc.IntegrityError as e:
            session.rollback()
            if "unique constraint" in str(e):
                raise exceptions.HttpException400(UNIQUE_ERROR_MESSAGE)
            raise exceptions.UnknownIntegrityError()

    session.refresh(orm_intermediatory_class_to_keyword_config)
    return schemas.IntermediatoryClassToKeywordConfigResponse.model_validate(
        orm_intermediatory_class_to_keyword_config
    )


def delete_intermediatory_class_to_keyword_config(
    session: sa.orm.Session,
    project_id: int,
    classifier_id: int,
    intermediatory_class_to_keyword_config_id: int,
) -> None:
    """Delete an intermediatory class to keyword config."""
    with crud.get_orm_classifier_with_edited_context(
        session, project_id, classifier_id
    ) as orm_classifier:
        orm_intermediatory_class_to_keyword_config = (
            session.query(models.IntermediatoryClassToKeywordConfig)
            .filter(
                models.IntermediatoryClassToKeywordConfig.id
                == intermediatory_class_to_keyword_config_id,
                models.IntermediatoryClassToKeywordConfig.classifier_id == orm_classifier.id,
            )
            .one_or_none()
        )
        if orm_intermediatory_class_to_keyword_config is None:
            raise exceptions.HttpException404(NOT_FOUND_ERROR_MESSAGE)

        session.delete(orm_intermediatory_class_to_keyword_config)
        session.commit()


def export_keyword_configs_csv(
    session: sa.orm.Session,
    project_id: int,
    classifier_id: int,
) -> str:
    """Export keyword classifier config as CSV string.

    Each row represents one keyword config (class_name, class_description, musts, nots).
    Classes with no keyword configs get a single row with empty musts and nots.
    """
    orm_classifier = crud.get_orm_classifier(session, project_id, classifier_id)
    if orm_classifier is None:
        raise exceptions.ClassifierNotFound()

    if orm_classifier.type != classifiers_base_schemas.ClassifierType.keyword_match:
        raise exceptions.HttpException400("The classifier is not a keyword match classifier.")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(CSV_HEADERS)

    # Build a set of class IDs that have keyword configs
    classes_with_configs: set[int] = set()
    for config in orm_classifier.intermediatory_class_to_keyword_configs:
        classes_with_configs.add(config.class_id)
        writer.writerow(
            [
                config.class_name,
                config.class_description,
                config.musts,
                config.nots or "",
                "true" if config.is_regex else "",
            ]
        )

    # Write classes that have no keyword configs
    for intermediatory_class in orm_classifier.intermediatory_classes:
        if intermediatory_class.id not in classes_with_configs:
            writer.writerow(
                [
                    intermediatory_class.name,
                    intermediatory_class.description,
                    "",
                    "",
                    "",
                ]
            )

    return output.getvalue()


def parse_and_validate_csv(file: BinaryIO) -> list[schemas.KeywordConfigCSVRow]:
    """Parse and validate a CSV file into a list of KeywordConfigCSVRow.

    Validates:
    - Required columns exist
    - Each row has a non-empty class_name
    - No duplicate (class_name, musts, nots) tuples
    - File is not empty (has at least headers)
    """
    try:
        text = file.read().decode("utf-8")
    except UnicodeDecodeError:
        raise exceptions.HttpException400("CSV file must be UTF-8 encoded.")

    if not text.strip():
        raise exceptions.HttpException400("CSV file is empty.")

    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        raise exceptions.HttpException400("CSV file is empty.")

    missing_columns = REQUIRED_CSV_COLUMNS - set(reader.fieldnames)
    if missing_columns:
        raise exceptions.HttpException400(
            f"CSV is missing required columns: {', '.join(sorted(missing_columns))}"
        )

    rows: list[schemas.KeywordConfigCSVRow] = []
    seen_tuples: set[tuple[str, str, str]] = set()

    for line_num, raw_row in enumerate(reader, start=2):
        try:
            is_regex_raw = raw_row.get("is_regex", "").strip().lower()
            is_regex = is_regex_raw in ("true", "1")
            row = schemas.KeywordConfigCSVRow(
                class_name=raw_row.get("class_name", ""),
                class_description=raw_row.get("class_description", ""),
                musts=raw_row.get("musts", ""),
                nots=raw_row.get("nots", ""),
                is_regex=is_regex,
            )
        except ValueError as e:
            raise exceptions.HttpException400(f"Row {line_num}: {e}")

        key = (row.class_name, row.musts, row.nots)
        # Only check for duplicates when musts or nots is non-empty (actual keyword config)
        if (row.musts or row.nots) and key in seen_tuples:
            raise exceptions.HttpException400(
                f"Row {line_num}: duplicate (class_name, musts, nots): {key}"
            )
        if row.musts or row.nots:
            seen_tuples.add(key)

        rows.append(row)

    return rows


def _create_classes_and_configs(
    session: sa.orm.Session,
    classifier_id: int,
    rows: list[schemas.KeywordConfigCSVRow],
    class_name_to_id: dict[str, int],
    existing_config_keys: set[tuple[int, str, str]],
) -> None:
    """Create intermediatory classes and keyword configs from parsed CSV rows.

    Args:
        session: SQLAlchemy session.
        classifier_id: Classifier ID.
        rows: Parsed CSV rows.
        class_name_to_id: Mapping of existing class names to IDs. New classes are added to this.
        existing_config_keys: Set of existing (class_id, musts, nots) tuples. Duplicates are
            skipped and new configs are added to this set.
    """
    # Deduplicate classes from CSV (first description wins, skip already-existing classes)
    class_name_to_description: dict[str, str] = {}
    for row in rows:
        if (
            row.class_name not in class_name_to_id
            and row.class_name not in class_name_to_description
        ):
            class_name_to_description[row.class_name] = row.class_description

    # Create new classes
    for class_name, class_description in class_name_to_description.items():
        orm_class = classifiers_models.IntermediatoryClasses(
            classifier_id=classifier_id,
            name=class_name,
            description=class_description,
        )
        session.add(orm_class)
        session.flush()
        class_name_to_id[class_name] = orm_class.id

    # Create keyword configs, skipping duplicates
    for row in rows:
        if not row.musts and not row.nots:
            continue
        class_id = class_name_to_id[row.class_name]
        config_key = (class_id, row.musts, row.nots)
        if config_key in existing_config_keys:
            continue
        orm_config = models.IntermediatoryClassToKeywordConfig(
            classifier_id=classifier_id,
            class_id=class_id,
            musts=row.musts,
            nots=row.nots,
            is_regex=row.is_regex,
        )
        session.add(orm_config)
        existing_config_keys.add(config_key)


def replace_via_csv(
    session: sa.orm.Session,
    project_id: int,
    classifier_id: int,
    rows: list[schemas.KeywordConfigCSVRow],
) -> None:
    """Replace all classes and keyword configs with data from parsed CSV rows.

    Deletes all existing IntermediatoryClassToKeywordConfig and IntermediatoryClasses
    for the classifier, then creates new ones from the CSV rows.
    """
    with crud.get_orm_classifier_with_edited_context(
        session, project_id, classifier_id
    ) as orm_classifier:
        try:
            # Delete all existing keyword configs for this classifier
            session.query(models.IntermediatoryClassToKeywordConfig).filter(
                models.IntermediatoryClassToKeywordConfig.classifier_id == orm_classifier.id,
            ).delete()

            # Delete all existing intermediatory classes for this classifier
            session.query(classifiers_models.IntermediatoryClasses).filter(
                classifiers_models.IntermediatoryClasses.classifier_id == orm_classifier.id,
            ).delete()

            session.flush()

            _create_classes_and_configs(session, orm_classifier.id, rows, {}, set())

            session.commit()
        except Exception:
            session.rollback()
            raise


def append_via_csv(
    session: sa.orm.Session,
    project_id: int,
    classifier_id: int,
    rows: list[schemas.KeywordConfigCSVRow],
) -> None:
    """Append classes and keyword configs from parsed CSV rows.

    Keeps all existing data. For each class_name in the CSV, reuses the existing class
    if one with that name already exists on the classifier, otherwise creates a new one.
    Skips keyword configs that would duplicate an existing (class_id, musts, nots) tuple.
    """
    with crud.get_orm_classifier_with_edited_context(
        session, project_id, classifier_id
    ) as orm_classifier:
        try:
            # Build lookup of existing class names to IDs
            existing_classes = (
                session.query(classifiers_models.IntermediatoryClasses)
                .filter(
                    classifiers_models.IntermediatoryClasses.classifier_id == orm_classifier.id,
                )
                .all()
            )
            class_name_to_id: dict[str, int] = {cls.name: cls.id for cls in existing_classes}

            # Build set of existing (class_id, musts, nots) tuples
            existing_configs = (
                session.query(models.IntermediatoryClassToKeywordConfig)
                .filter(
                    models.IntermediatoryClassToKeywordConfig.classifier_id == orm_classifier.id,
                )
                .all()
            )
            existing_config_keys: set[tuple[int, str, str]] = {
                (cfg.class_id, cfg.musts, cfg.nots) for cfg in existing_configs
            }

            _create_classes_and_configs(
                session, orm_classifier.id, rows, class_name_to_id, existing_config_keys
            )

            session.commit()
        except Exception:
            session.rollback()
            raise


def import_keyword_configs_csv(
    session: sa.orm.Session,
    project_id: int,
    classifier_id: int,
    file: BinaryIO,
    import_mode: schemas.ImportMode,
) -> schemas.KeywordMatchClassifierDetail:
    """Import keyword configs from a CSV file.

    Parses and validates the CSV, then dispatches to replace or append mode.
    Returns the refreshed classifier detail.
    """
    rows = parse_and_validate_csv(file)

    if import_mode == schemas.ImportMode.replace:
        replace_via_csv(session, project_id, classifier_id, rows)
    elif import_mode == schemas.ImportMode.append:
        append_via_csv(session, project_id, classifier_id, rows)

    orm_classifier = crud.get_orm_classifier(session, project_id, classifier_id)
    session.refresh(orm_classifier)
    return schemas.KeywordMatchClassifierDetail.model_validate(obj=orm_classifier)
