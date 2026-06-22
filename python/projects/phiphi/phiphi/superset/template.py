"""Dashboard template transformation."""

import io
import re
import uuid
import zipfile
from pathlib import Path
from typing import Any

import yaml

from phiphi import config
from phiphi.superset import constants


def _build_uuid_map(template_path: Path, glob_pattern: str) -> dict[str, str]:
    """Build a mapping of old UUIDs to new UUIDs from template files.

    Args:
        template_path: Path to template export directory.
        glob_pattern: Glob pattern to match files.

    Returns:
        Mapping of old UUIDs to new UUIDs.
    """
    uuid_map: dict[str, str] = {}
    for file_path in template_path.glob(glob_pattern):
        content = yaml.safe_load(file_path.read_text())
        old_uuid = content.get("uuid")
        if old_uuid:
            uuid_map[old_uuid] = str(uuid.uuid4())
    return uuid_map


def _extract_catalog_from_uri(sqlalchemy_uri: str) -> str:
    """Extract BigQuery catalog/project from SQLAlchemy URI.

    Args:
        sqlalchemy_uri: SQLAlchemy URI (format: bigquery://PROJECT/DATASET).

    Returns:
        BigQuery catalog/project name.

    Raises:
        ValueError: If a URI format is invalid.
    """
    if not sqlalchemy_uri:
        msg = "SUPERSET_DATABASE_SQLALCHEMY_URI is not configured"
        raise ValueError(msg)
    if not sqlalchemy_uri.startswith("bigquery://"):
        msg = f"Invalid SQLAlchemy URI format: {sqlalchemy_uri}"
        raise ValueError(msg)
    uri_path = sqlalchemy_uri.replace("bigquery://", "")
    catalog = uri_path.split("/")[0]
    if not catalog:
        msg = f"Could not extract catalog from URI: {sqlalchemy_uri}"
        raise ValueError(msg)

    return catalog


def _write_template_file_to_zip(
    zf: zipfile.ZipFile,
    file_path: Path,
    template_path: Path,
    project_namespace: str,
    project_name: str,
    project_id: int,
    dataset_uuid_map: dict[str, str],
    chart_uuid_map: dict[str, str],
    dashboard_uuid: str,
    db_uuid: str,
    db_catalog: str,
    export_dir: str = "export",
) -> None:
    """Write a single template file to the ZIP, transforming if needed.

    Args:
        zf: ZipFile to write to.
        file_path: Path to the file to write.
        template_path: Path to template export directory.
        project_namespace: Project namespace (e.g., "project_id123").
        project_name: Project name for dashboard title.
        project_id: Project ID for dashboard title.
        dataset_uuid_map: Mapping of old dataset UUIDs to new UUIDs.
        chart_uuid_map: Mapping of old chart UUIDs to new UUIDs.
        dashboard_uuid: New UUID for the dashboard.
        db_uuid: UUID of the database connection.
        db_catalog: BigQuery catalog/project name.
        export_dir: Root directory name in the ZIP file.
    """
    relative_path = file_path.relative_to(template_path)
    # Use POSIX-style paths (forward slashes) for ZIP compatibility
    # Adding the export_dir as the root directory, this is a specific need from Superset
    # and is not a general requirement for ZIP files.
    # Superset expects a folder structure like below upon unzipping an export directory.
    # export_zip.zip: unzips to: export_zip/datasets/dataset_1.yaml,
    # export_zip/charts/chart_1.yaml, etc.
    # Not: export_zip.zip: unzips to: datasets/dataset_1.yaml, charts/chart_1.yaml, etc.
    zip_path = f"{export_dir}/{relative_path.as_posix()}"

    # Determine if this file needs transformation
    needs_transform = file_path.suffix == ".yaml" and (
        "datasets/" in zip_path
        or "charts/" in zip_path
        or "dashboards/" in zip_path
        or "databases/" in zip_path
    )

    # Write files that don't need transformation directly (preserves exact format)
    if not needs_transform:
        zf.writestr(zip_path, file_path.read_bytes())
        return

    # Transform and write YAML files that need modification
    content = yaml.safe_load(file_path.read_text())

    if "datasets/" in zip_path:
        content = _transform_dataset(
            content, project_namespace, dataset_uuid_map, db_uuid, db_catalog
        )
    elif "charts/" in zip_path:
        content = _transform_chart(content, dataset_uuid_map, chart_uuid_map)
    elif "dashboards/" in zip_path:
        content = _transform_dashboard(
            content, project_name, project_id, dashboard_uuid, dataset_uuid_map, chart_uuid_map
        )
    elif "databases/" in zip_path:
        content = _transform_database(content, db_uuid)

    zf.writestr(
        zip_path,
        yaml.dump(content, default_flow_style=False, allow_unicode=True),
    )


def create_project_dashboard_zip(
    project_id: int,
    project_name: str,
    template_path: Path | None = None,
    database_uuid: str | None = None,
) -> bytes:
    """Create customized dashboard ZIP for a project.

    Args:
        project_id: Project ID (used for schema name project_id{N}).
        project_name: Human-readable name (for dashboard title).
        template_path: Path to template export directory.
        database_uuid: UUID of shared BigQuery database in Superset.

    Returns:
        ZIP file as bytes ready for import.
    """
    template_path = template_path or constants.TEMPLATE_PATH
    project_namespace = f"project_id{project_id}"
    db_uuid = database_uuid or config.settings.SUPERSET_DATABASE_UUID
    # Extract catalog from SQLAlchemy URI (format: bigquery://PROJECT/DATASET)
    db_sqlalchemy_uri = config.settings.SUPERSET_DATABASE_SQLALCHEMY_URI
    db_catalog = _extract_catalog_from_uri(db_sqlalchemy_uri)
    # Use a unique export directory name based on projects
    export_dir = f"project_{project_id}_{project_name.replace(' ', '_').lower()}"

    dataset_uuid_map = _build_uuid_map(template_path, "datasets/**/*.yaml")
    chart_uuid_map = _build_uuid_map(template_path, "charts/*.yaml")
    dashboard_uuid = str(uuid.uuid4())

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in template_path.rglob("*"):
            if file_path.is_dir():
                continue
            _write_template_file_to_zip(
                zf,
                file_path,
                template_path,
                project_namespace,
                project_name,
                project_id,
                dataset_uuid_map,
                chart_uuid_map,
                dashboard_uuid,
                db_uuid,
                db_catalog,
                export_dir,
            )

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def _transform_dataset(
    content: dict[str, Any],
    project_namespace: str,
    uuid_map: dict[str, str],
    database_uuid: str,
    catalog: str,
) -> dict[str, Any]:
    """Transform dataset YAML for new project.

    Args:
        content: Dataset YAML content.
        project_namespace: Project namespace (e.g., "project_id123").
        uuid_map: Mapping of old UUIDs to new UUIDs.
        database_uuid: UUID of the database connection.
        catalog: BigQuery catalog/project name.

    Returns:
        Transformed dataset content.
    """
    # Recursively transform any nested UUID references
    content = _recursive_transform(content, uuid_map, {})
    # Set environment-specific fields
    content["schema"] = project_namespace
    content["database_uuid"] = database_uuid
    content["catalog"] = catalog
    return content


def _transform_database(
    content: dict[str, Any],
    database_uuid: str,
) -> dict[str, Any]:
    """Transform database YAML to use existing database UUID.

    Args:
        content: Database YAML content.
        database_uuid: UUID of the existing database connection in Superset.

    Returns:
        Transformed database content with the target UUID.
    """
    content["uuid"] = database_uuid
    return content


def _transform_chart(
    content: dict[str, Any],
    dataset_uuid_map: dict[str, str],
    chart_uuid_map: dict[str, str],
) -> dict[str, Any]:
    """Transform chart YAML for new dataset references.

    Args:
        content: Chart YAML content.
        dataset_uuid_map: Mapping of old dataset UUIDs to new UUIDs.
        chart_uuid_map: Mapping of old chart UUIDs to new UUIDs.

    Returns:
        Transformed chart content.
    """
    content = _recursive_transform(content, dataset_uuid_map, chart_uuid_map)
    # Remove stale query_context which may contain old numeric IDs
    if "query_context" in content:
        content["query_context"] = None
    return content


def _transform_dashboard(
    content: dict[str, Any],
    project_name: str,
    project_id: int,
    new_uuid: str,
    dataset_uuid_map: dict[str, str],
    chart_uuid_map: dict[str, str],
) -> dict[str, Any]:
    """Transform dashboard YAML for new project.

    Args:
        content: Dashboard YAML content.
        project_name: Project name for the dashboard title.
        project_id: Project ID for the dashboard title.
        new_uuid: New UUID for the dashboard.
        dataset_uuid_map: Mapping of old dataset UUIDs to new UUIDs.
        chart_uuid_map: Mapping of old chart UUIDs to new UUIDs.

    Returns:
        Transformed dashboard content.
    """
    content["uuid"] = new_uuid
    content["dashboard_title"] = get_dashboard_title(project_name, project_id)
    content["published"] = True

    content = _recursive_transform(content, dataset_uuid_map, chart_uuid_map)
    return content


def _recursive_transform(
    data: Any,
    dataset_uuid_map: dict[str, str],
    chart_uuid_map: dict[str, str],
) -> Any:
    """Recursively remap dataset/chart UUID references inside nested structures."""
    dataset_keys = {"datasetUuid", "dataset_uuid"}

    if isinstance(data, dict):
        new_uuids: dict[str, Any] = {}
        for key, value in data.items():
            if key in dataset_keys:
                new_uuids[key] = dataset_uuid_map.get(value, value)
            elif key == "uuid":
                # Try chart map first, then dataset map, default to original
                new_uuids[key] = chart_uuid_map.get(value, dataset_uuid_map.get(value, value))
            else:
                new_uuids[key] = _recursive_transform(value, dataset_uuid_map, chart_uuid_map)
        return new_uuids

    if isinstance(data, list):
        return [_recursive_transform(item, dataset_uuid_map, chart_uuid_map) for item in data]

    return data


# Maximum number of characters taken from the project name in the dashboard title.
# Kept to a reasonable length to avoid very long display titles.
_MAX_PROJECT_NAME_LENGTH = 100

# FAB enforces a 64-character column limit on role names.
# Role names use the format "{project_id} View {dashboard_title}" so they are unique
# and identifiable even when the title is truncated to fit within this limit.
_FAB_ROLE_NAME_MAX_LENGTH = 64


def get_dashboard_title(project_name: str, project_id: int) -> str:
    """Get the dashboard title for a project.

    The title is sanitised before use because it feeds directly into Superset provisioning:
    - Special characters (anything other than word characters, spaces, and hyphens) are
      stripped. Superset's FAB role name validator rejects names containing characters such
      as '!', '@', '#' etc., causing a 422 error when the role is created.
    - The project name is truncated to _MAX_PROJECT_NAME_LENGTH characters to avoid
      excessively long display titles.

    Args:
        project_name: Project name.
        project_id: Project ID.

    Returns:
        Formatted dashboard title.
    """
    sanitized = re.sub(r"[^\w\s-]", "", project_name)
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    sanitized = sanitized[:_MAX_PROJECT_NAME_LENGTH]
    return f"{sanitized} ({project_id})"


def get_superset_role_name(project_id: int, role_type: str, dashboard_title: str) -> str:
    """Get the Superset role name for a project.

    Format: "{project_id} {role_type} {dashboard_title}" truncated to
    _FAB_ROLE_NAME_MAX_LENGTH characters. Putting the project_id first ensures the
    role is identifiable even when the title is truncated to fit FAB's column limit.

    Args:
        project_id: Project ID.
        role_type: Role type label, e.g. "View" or "Edit".
        dashboard_title: Dashboard title from get_dashboard_title.

    Returns:
        Role name truncated to _FAB_ROLE_NAME_MAX_LENGTH characters.
    """
    return f"{project_id} {role_type} {dashboard_title}"[:_FAB_ROLE_NAME_MAX_LENGTH]
