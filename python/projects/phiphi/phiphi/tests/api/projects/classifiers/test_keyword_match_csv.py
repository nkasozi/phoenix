"""Tests for keyword match CSV export and import."""

import csv
import io
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from phiphi.api import exceptions
from phiphi.api.projects import classifiers
from phiphi.api.projects.classifiers import base_schemas
from phiphi.api.projects.classifiers.keyword_match import crud
from phiphi.seed.classifiers import keyword_match_seed


def _parse_csv(csv_string: str) -> list[dict[str, str]]:
    """Parse a CSV string into a list of dicts."""
    reader = csv.DictReader(io.StringIO(csv_string))
    return list(reader)


def test_export_classifier_with_full_data(reseed_tables) -> None:
    """Test export a classifier with classes and keyword configs."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]

    csv_string = crud.export_keyword_configs_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )
    rows = _parse_csv(csv_string)

    assert len(rows) == 2
    assert rows[0]["class_name"] == "Test Class 1"
    assert rows[0]["class_description"] == "Test Class 1 Description"
    assert rows[0]["musts"] == "test1"
    assert rows[0]["nots"] == ""
    assert rows[0]["is_regex"] == ""
    assert rows[1]["class_name"] == "Test Class 2"
    assert rows[1]["class_description"] == "Test Class 2 Description"
    assert rows[1]["musts"] == "test2"
    assert rows[1]["nots"] == ""
    assert rows[1]["is_regex"] == ""


def test_export_empty_classifier(reseed_tables) -> None:
    """Test export a classifier with no classes returns only headers."""
    classifier = classifiers.crud.create_classifier(
        session=reseed_tables,
        project_id=1,
        classifier_type=base_schemas.ClassifierType.keyword_match,
        classifier_create=base_schemas.ClassifierWithIntermediatoryCreate(
            name="Empty Classifier",
            description="No classes",
            intermediatory_classes=[],
        ),
    )

    csv_string = crud.export_keyword_configs_csv(
        session=reseed_tables,
        project_id=1,
        classifier_id=classifier.id,
    )
    rows = _parse_csv(csv_string)

    assert len(rows) == 0
    assert "class_name" in csv_string


def test_export_classes_without_keyword_configs(reseed_tables) -> None:
    """Test export a classifier with classes but no keyword configs."""
    # The versioned classifier has classes but no intermediatory keyword configs
    # (configs were snapshotted into the version, not kept as intermediatory)
    classifier = classifiers.crud.create_classifier(
        session=reseed_tables,
        project_id=1,
        classifier_type=base_schemas.ClassifierType.keyword_match,
        classifier_create=base_schemas.ClassifierWithIntermediatoryCreate(
            name="Classes Only Classifier",
            description="Has classes but no configs",
            intermediatory_classes=[
                base_schemas.IntermediatoryClassCreate(
                    name="Lonely Class",
                    description="No keywords",
                ),
            ],
        ),
    )

    csv_string = crud.export_keyword_configs_csv(
        session=reseed_tables,
        project_id=1,
        classifier_id=classifier.id,
    )
    rows = _parse_csv(csv_string)

    assert len(rows) == 1
    assert rows[0]["class_name"] == "Lonely Class"
    assert rows[0]["class_description"] == "No keywords"
    assert rows[0]["musts"] == ""
    assert rows[0]["nots"] == ""
    assert rows[0]["is_regex"] == ""


def test_export_nonexistent_classifier(reseed_tables) -> None:
    """Test export a non-existent classifier raises ClassifierNotFound."""
    with pytest.raises(exceptions.ClassifierNotFound):
        crud.export_keyword_configs_csv(
            session=reseed_tables,
            project_id=1,
            classifier_id=999999,
        )


def test_export_csv_route(reseed_tables, client_admin: TestClient) -> None:
    """Test GET export_csv route returns CSV with correct content type."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]
    response = client_admin.get(
        f"/projects/{classifier.project_id}/classifiers/keyword_match/{classifier.id}/export_csv"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert (
        f"keyword_classifier_export_project_{classifier.project_id}_classifier_{classifier.id}.csv"
        in response.headers["content-disposition"]
    )

    rows = _parse_csv(response.text)
    assert len(rows) == 2
    assert rows[0]["class_name"] == "Test Class 1"
    assert rows[0]["musts"] == "test1"


def test_export_csv_route_nonexistent_classifier(reseed_tables, client_admin: TestClient) -> None:
    """Test GET export_csv route returns 404 for non-existent classifier."""
    response = client_admin.get("/projects/1/classifiers/keyword_match/999999/export_csv")
    assert response.status_code == 404


def test_export_csv_route_no_auth(reseed_tables, client_no_user: TestClient) -> None:
    """Test GET export_csv route returns 401 for unauthenticated user."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]
    response = client_no_user.get(
        f"/projects/{classifier.project_id}/classifiers/keyword_match/{classifier.id}/export_csv"
    )
    assert response.status_code == 401


def test_export_csv_route_user_access(reseed_tables, client_user_1: TestClient) -> None:
    """Test GET export_csv route succeeds for user with project access."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]
    response = client_user_1.get(
        f"/projects/{classifier.project_id}/classifiers/keyword_match/{classifier.id}/export_csv"
    )
    assert response.status_code == 200


# --- CSV parsing and validation tests ---


def _make_csv_bytes(header: str, *rows: str) -> io.BytesIO:
    """Helper to create a CSV BytesIO from header and row strings."""
    content = "\n".join([header] + list(rows))
    return io.BytesIO(content.encode("utf-8"))


def test_parse_and_validate_csv_valid() -> None:
    """Test parsing a valid CSV file."""
    file = _make_csv_bytes(
        "class_name,class_description,musts,nots",
        "Class A,Description A,keyword1,bad_word",
        "Class A,Description A,keyword2,",
        "Class B,Description B,keyword3,",
    )
    rows = crud.parse_and_validate_csv(file)

    assert len(rows) == 3
    assert rows[0].class_name == "Class A"
    assert rows[0].class_description == "Description A"
    assert rows[0].musts == "keyword1"
    assert rows[0].nots == "bad_word"
    assert rows[1].musts == "keyword2"
    assert rows[2].class_name == "Class B"


def test_parse_and_validate_csv_missing_columns() -> None:
    """Test parsing a CSV with missing required columns raises 400."""
    file = _make_csv_bytes(
        "musts,nots",
        "keyword1,",
    )
    with pytest.raises(exceptions.HttpException400, match="missing required columns"):
        crud.parse_and_validate_csv(file)


def test_parse_and_validate_csv_empty_class_name() -> None:
    """Test parsing a CSV with empty class_name raises 400."""
    file = _make_csv_bytes(
        "class_name,class_description,musts,nots",
        ",Description A,keyword1,",
    )
    with pytest.raises(exceptions.HttpException400, match="Row 2"):
        crud.parse_and_validate_csv(file)


def test_parse_and_validate_csv_duplicate_rows() -> None:
    """Test parsing a CSV with duplicate (class_name, musts, nots) raises 400."""
    file = _make_csv_bytes(
        "class_name,class_description,musts,nots",
        "Class A,Description A,keyword1,bad_word",
        "Class A,Description A,keyword1,bad_word",
    )
    with pytest.raises(exceptions.HttpException400, match="duplicate"):
        crud.parse_and_validate_csv(file)


def test_parse_and_validate_csv_empty_file() -> None:
    """Test parsing an empty CSV file raises 400."""
    file = io.BytesIO(b"")
    with pytest.raises(exceptions.HttpException400, match="empty"):
        crud.parse_and_validate_csv(file)


def test_parse_and_validate_csv_headers_only() -> None:
    """Test parsing a CSV with only headers returns empty list."""
    file = _make_csv_bytes("class_name,class_description,musts,nots")
    rows = crud.parse_and_validate_csv(file)
    assert len(rows) == 0


def test_parse_csv_with_quoted_commas() -> None:
    """Test parsing CSV where values contain commas inside quotes."""
    file = _make_csv_bytes(
        "class_name,class_description,musts,nots",
        '"Class, With Comma","Description, also commas",keyword1,',
    )
    rows = crud.parse_and_validate_csv(file)

    assert len(rows) == 1
    assert rows[0].class_name == "Class, With Comma"
    assert rows[0].class_description == "Description, also commas"
    assert rows[0].musts == "keyword1"


def test_parse_csv_with_quoted_newlines() -> None:
    """Test parsing CSV where values contain newlines inside quotes."""
    # csv.DictReader handles quoted newlines correctly
    content = (
        "class_name,class_description,musts,nots\n"
        '"Multi\nLine Class","Description\nwith newline",keyword1,'
    )
    file = io.BytesIO(content.encode("utf-8"))
    rows = crud.parse_and_validate_csv(file)

    assert len(rows) == 1
    assert rows[0].class_name == "Multi\nLine Class"
    assert rows[0].musts == "keyword1"


def test_parse_csv_with_escaped_quotes() -> None:
    """Test parsing CSV where values contain escaped double quotes."""
    file = _make_csv_bytes(
        "class_name,class_description,musts,nots",
        '"Class ""Quoted""","A ""special"" description",keyword1,',
    )
    rows = crud.parse_and_validate_csv(file)

    assert len(rows) == 1
    assert rows[0].class_name == 'Class "Quoted"'
    assert rows[0].class_description == 'A "special" description'


# --- Replace import mode tests ---


def test_replace_via_csv(reseed_tables) -> None:
    """Test replace import replaces all existing classes and configs."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]

    # Verify existing data before replace
    csv_before = crud.export_keyword_configs_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )
    rows_before = _parse_csv(csv_before)
    assert len(rows_before) == 2

    # Import new data via replace (3 rows instead of 2 to verify count changes)
    new_rows = crud.parse_and_validate_csv(
        _make_csv_bytes(
            "class_name,class_description,musts,nots",
            "New Class X,Desc X,keyword_x,",
            "New Class X,Desc X,keyword_x2,bad_x",
            "New Class Y,Desc Y,keyword_y,bad_y",
        )
    )
    crud.replace_via_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
        rows=new_rows,
    )

    # Verify old data is gone and new data is present
    csv_after = crud.export_keyword_configs_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )
    rows_after = _parse_csv(csv_after)
    assert len(rows_after) == 3
    assert rows_after[0]["class_name"] == "New Class X"
    assert rows_after[0]["musts"] == "keyword_x"
    assert rows_after[1]["class_name"] == "New Class X"
    assert rows_after[1]["musts"] == "keyword_x2"
    assert rows_after[1]["nots"] == "bad_x"
    assert rows_after[2]["class_name"] == "New Class Y"
    assert rows_after[2]["musts"] == "keyword_y"
    assert rows_after[2]["nots"] == "bad_y"


def test_replace_via_csv_deduplicates_classes(reseed_tables) -> None:
    """Test replace deduplicates classes by name, uses first description."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]

    new_rows = crud.parse_and_validate_csv(
        _make_csv_bytes(
            "class_name,class_description,musts,nots",
            "Same Class,First Description,keyword1,",
            "Same Class,Second Description,keyword2,",
        )
    )
    crud.replace_via_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
        rows=new_rows,
    )

    csv_after = crud.export_keyword_configs_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )
    rows_after = _parse_csv(csv_after)
    assert len(rows_after) == 2
    # Both rows should have the same class with first description
    assert rows_after[0]["class_description"] == "First Description"
    assert rows_after[1]["class_description"] == "First Description"


def test_replace_via_csv_updates_last_edited_at(reseed_tables) -> None:
    """Test replace updates last_edited_at on the classifier."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]

    # Get last_edited_at before
    detail_before = classifiers.crud.get_classifier(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )
    assert detail_before is not None
    last_edited_before = detail_before.last_edited_at

    new_rows = crud.parse_and_validate_csv(
        _make_csv_bytes(
            "class_name,class_description,musts,nots",
            "Class Z,Desc Z,keyword_z,",
        )
    )
    crud.replace_via_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
        rows=new_rows,
    )

    detail_after = classifiers.crud.get_classifier(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )
    assert detail_after is not None
    assert detail_after.last_edited_at is not None
    if last_edited_before is not None:
        assert detail_after.last_edited_at >= last_edited_before


def test_replace_via_csv_round_trip(reseed_tables) -> None:
    """Test export -> replace -> export produces identical CSV."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]

    # First replace with known data
    initial_rows = crud.parse_and_validate_csv(
        _make_csv_bytes(
            "class_name,class_description,musts,nots",
            "Class A,Desc A,keyword1,bad1",
            "Class A,Desc A,keyword2,",
            "Class B,Desc B,keyword3,",
        )
    )
    crud.replace_via_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
        rows=initial_rows,
    )

    # Export
    csv_export_1 = crud.export_keyword_configs_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )

    # Replace with the exported CSV
    exported_rows = crud.parse_and_validate_csv(io.BytesIO(csv_export_1.encode("utf-8")))
    crud.replace_via_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
        rows=exported_rows,
    )

    # Export again and compare
    csv_export_2 = crud.export_keyword_configs_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )
    assert csv_export_1 == csv_export_2


def test_replace_via_csv_rollback_on_error(reseed_tables) -> None:
    """Test replace rolls back if an error occurs after flush but before commit."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]

    # Capture the data before the failed replace
    csv_before = crud.export_keyword_configs_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )

    new_rows = crud.parse_and_validate_csv(
        _make_csv_bytes(
            "class_name,class_description,musts,nots",
            "Should Not Persist,Desc,keyword_fail,",
        )
    )

    # Patch session.commit to raise after the deletes and flushes have happened
    original_commit = reseed_tables.commit
    call_count = 0

    def failing_commit():
        nonlocal call_count
        call_count += 1
        # The first commit call inside replace_via_csv is the one we want to fail
        if call_count == 1:
            raise RuntimeError("Simulated commit failure")
        return original_commit()

    with mock.patch.object(reseed_tables, "commit", side_effect=failing_commit):
        with pytest.raises(RuntimeError, match="Simulated commit failure"):
            crud.replace_via_csv(
                session=reseed_tables,
                project_id=classifier.project_id,
                classifier_id=classifier.id,
                rows=new_rows,
            )

    # Verify original data is intact after rollback
    csv_after = crud.export_keyword_configs_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )
    assert csv_before == csv_after


def test_replace_via_csv_with_quoted_values(reseed_tables) -> None:
    """Test replace round-trips correctly with values that need quoting."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]

    new_rows = crud.parse_and_validate_csv(
        _make_csv_bytes(
            "class_name,class_description,musts,nots",
            '"Class, Commas","Desc with ""quotes""",keyword1,',
        )
    )
    crud.replace_via_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
        rows=new_rows,
    )

    csv_after = crud.export_keyword_configs_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )
    rows_after = _parse_csv(csv_after)
    assert len(rows_after) == 1
    assert rows_after[0]["class_name"] == "Class, Commas"
    assert rows_after[0]["class_description"] == 'Desc with "quotes"'


# --- Append import mode tests ---


def test_append_via_csv_into_empty_classifier(reseed_tables) -> None:
    """Test append into a classifier with no classes creates everything."""
    classifier = classifiers.crud.create_classifier(
        session=reseed_tables,
        project_id=1,
        classifier_type=base_schemas.ClassifierType.keyword_match,
        classifier_create=base_schemas.ClassifierWithIntermediatoryCreate(
            name="Append Empty Classifier",
            description="Empty for append test",
            intermediatory_classes=[],
        ),
    )

    new_rows = crud.parse_and_validate_csv(
        _make_csv_bytes(
            "class_name,class_description,musts,nots",
            "Class A,Desc A,keyword1,",
            "Class B,Desc B,keyword2,bad2",
        )
    )
    crud.append_via_csv(
        session=reseed_tables,
        project_id=1,
        classifier_id=classifier.id,
        rows=new_rows,
    )

    csv_after = crud.export_keyword_configs_csv(
        session=reseed_tables,
        project_id=1,
        classifier_id=classifier.id,
    )
    rows_after = _parse_csv(csv_after)
    assert len(rows_after) == 2
    assert rows_after[0]["class_name"] == "Class A"
    assert rows_after[0]["musts"] == "keyword1"
    assert rows_after[1]["class_name"] == "Class B"
    assert rows_after[1]["nots"] == "bad2"


def test_append_via_csv_adds_new_skips_duplicates(reseed_tables) -> None:
    """Test append adds new configs and skips duplicates."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]

    # First set up known state via replace
    crud.replace_via_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
        rows=crud.parse_and_validate_csv(
            _make_csv_bytes(
                "class_name,class_description,musts,nots",
                "Class A,Desc A,existing_keyword,",
            )
        ),
    )

    # Append: one duplicate, one new config, one new class
    append_rows = crud.parse_and_validate_csv(
        _make_csv_bytes(
            "class_name,class_description,musts,nots",
            "Class A,Desc A,existing_keyword,",
            "Class A,Desc A,new_keyword,",
            "Class B,Desc B,keyword_b,",
        )
    )
    crud.append_via_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
        rows=append_rows,
    )

    csv_after = crud.export_keyword_configs_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )
    rows_after = _parse_csv(csv_after)
    assert len(rows_after) == 3
    assert rows_after[0]["class_name"] == "Class A"
    assert rows_after[0]["musts"] == "existing_keyword"
    assert rows_after[1]["class_name"] == "Class A"
    assert rows_after[1]["musts"] == "new_keyword"
    assert rows_after[2]["class_name"] == "Class B"
    assert rows_after[2]["musts"] == "keyword_b"


def test_append_via_csv_reuses_existing_class(reseed_tables) -> None:
    """Test append reuses an existing class by name rather than creating a new one."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]

    # Set up known state
    crud.replace_via_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
        rows=crud.parse_and_validate_csv(
            _make_csv_bytes(
                "class_name,class_description,musts,nots",
                "Reuse Class,Original Desc,keyword1,",
            )
        ),
    )

    # Append with same class name but different description — should reuse existing class
    append_rows = crud.parse_and_validate_csv(
        _make_csv_bytes(
            "class_name,class_description,musts,nots",
            "Reuse Class,Different Desc,keyword2,",
        )
    )
    crud.append_via_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
        rows=append_rows,
    )

    csv_after = crud.export_keyword_configs_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )
    rows_after = _parse_csv(csv_after)
    assert len(rows_after) == 2
    # Both should have original description since the class was reused
    assert rows_after[0]["class_description"] == "Original Desc"
    assert rows_after[1]["class_description"] == "Original Desc"
    assert rows_after[0]["musts"] == "keyword1"
    assert rows_after[1]["musts"] == "keyword2"


def test_append_via_csv_updates_last_edited_at(reseed_tables) -> None:
    """Test append updates last_edited_at on the classifier."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]

    detail_before = classifiers.crud.get_classifier(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )
    assert detail_before is not None
    last_edited_before = detail_before.last_edited_at

    append_rows = crud.parse_and_validate_csv(
        _make_csv_bytes(
            "class_name,class_description,musts,nots",
            "Append Class,Desc,append_kw,",
        )
    )
    crud.append_via_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
        rows=append_rows,
    )

    detail_after = classifiers.crud.get_classifier(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )
    assert detail_after is not None
    assert detail_after.last_edited_at is not None
    if last_edited_before is not None:
        assert detail_after.last_edited_at >= last_edited_before


# --- Import CSV route tests ---


def _upload_csv(
    client: TestClient, project_id: int, classifier_id: int, csv_content: str, import_mode: str
):
    """Helper to POST a CSV file to the import endpoint."""
    return client.post(
        f"/projects/{project_id}/classifiers/keyword_match/{classifier_id}/import_csv",
        params={"import_mode": import_mode},
        files={"file": ("import.csv", csv_content.encode("utf-8"), "text/csv")},
    )


def test_import_csv_route_replace(reseed_tables, client_admin: TestClient) -> None:
    """Test POST import_csv with replace mode returns updated classifier detail."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]
    csv_content = "class_name,class_description,musts,nots\nNew Class,Desc,new_kw,"
    response = _upload_csv(
        client_admin, classifier.project_id, classifier.id, csv_content, "replace"
    )

    assert response.status_code == 200
    json = response.json()
    assert len(json["intermediatory_classes"]) == 1
    assert json["intermediatory_classes"][0]["name"] == "New Class"
    assert len(json["intermediatory_class_to_keyword_configs"]) == 1
    assert json["intermediatory_class_to_keyword_configs"][0]["musts"] == "new_kw"


def test_import_csv_route_append(reseed_tables, client_admin: TestClient) -> None:
    """Test POST import_csv with append mode returns updated classifier detail."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]

    # First replace to set known state
    _upload_csv(
        client_admin,
        classifier.project_id,
        classifier.id,
        "class_name,class_description,musts,nots\nClass A,Desc A,kw1,",
        "replace",
    )

    # Then append
    csv_content = (
        "class_name,class_description,musts,nots\nClass A,Desc A,kw2,\nClass B,Desc B,kw3,"
    )
    response = _upload_csv(
        client_admin, classifier.project_id, classifier.id, csv_content, "append"
    )

    assert response.status_code == 200
    json = response.json()
    assert len(json["intermediatory_classes"]) == 2
    assert len(json["intermediatory_class_to_keyword_configs"]) == 3


def test_import_csv_route_nonexistent_classifier(reseed_tables, client_admin: TestClient) -> None:
    """Test POST import_csv returns 404 for non-existent classifier."""
    csv_content = "class_name,class_description,musts,nots\nClass A,Desc,kw,"
    response = _upload_csv(client_admin, 1, 999999, csv_content, "replace")
    assert response.status_code == 404


def test_import_csv_route_invalid_csv(reseed_tables, client_admin: TestClient) -> None:
    """Test POST import_csv returns 400 for invalid CSV."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]
    csv_content = "wrong_header,bad\nvalue,value"
    response = _upload_csv(
        client_admin, classifier.project_id, classifier.id, csv_content, "replace"
    )
    assert response.status_code == 400


def test_import_csv_route_no_auth(reseed_tables, client_no_user: TestClient) -> None:
    """Test POST import_csv returns 401 for unauthenticated user."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]
    csv_content = "class_name,class_description,musts,nots\nClass A,Desc,kw,"
    response = _upload_csv(
        client_no_user, classifier.project_id, classifier.id, csv_content, "replace"
    )
    assert response.status_code == 401


def test_import_csv_route_user_access(reseed_tables, client_user_1: TestClient) -> None:
    """Test POST import_csv succeeds for user with project access."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]
    csv_content = "class_name,class_description,musts,nots\nClass A,Desc,kw,"
    response = _upload_csv(
        client_user_1, classifier.project_id, classifier.id, csv_content, "replace"
    )
    assert response.status_code == 200


# --- is_regex CSV tests ---


def test_parse_csv_with_is_regex_column() -> None:
    """Test parsing a CSV with is_regex column."""
    file = _make_csv_bytes(
        "class_name,class_description,musts,nots,is_regex",
        "Class A,Desc A,(?i)foo[0-9]+,,true",
        "Class B,Desc B,keyword,,",
    )
    rows = crud.parse_and_validate_csv(file)
    assert len(rows) == 2
    assert rows[0].is_regex is True
    assert rows[1].is_regex is False


def test_parse_csv_without_is_regex_column_defaults_false() -> None:
    """Test backwards compat: CSV without is_regex column defaults to False."""
    file = _make_csv_bytes(
        "class_name,class_description,musts,nots",
        "Class A,Desc A,keyword1,",
    )
    rows = crud.parse_and_validate_csv(file)
    assert len(rows) == 1
    assert rows[0].is_regex is False


def test_parse_csv_is_regex_accepts_1() -> None:
    """Test that is_regex accepts '1' as truthy."""
    file = _make_csv_bytes(
        "class_name,class_description,musts,nots,is_regex",
        "Class A,Desc A,(?i)pattern,,1",
    )
    rows = crud.parse_and_validate_csv(file)
    assert rows[0].is_regex is True


def test_replace_via_csv_with_is_regex(reseed_tables) -> None:
    """Test replace import with is_regex rows exports correctly."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]

    new_rows = crud.parse_and_validate_csv(
        _make_csv_bytes(
            "class_name,class_description,musts,nots,is_regex",
            "Regex Class,Desc,(?i)[g9][e3]nder,,true",
            "Normal Class,Desc,keyword,,",
        )
    )
    crud.replace_via_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
        rows=new_rows,
    )

    csv_after = crud.export_keyword_configs_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )
    rows_after = _parse_csv(csv_after)
    assert len(rows_after) == 2
    assert rows_after[0]["is_regex"] == "true"
    assert rows_after[0]["musts"] == "(?i)[g9][e3]nder"
    assert rows_after[1]["is_regex"] == ""


def test_replace_via_csv_is_regex_round_trip(reseed_tables) -> None:
    """Test export -> replace -> export round-trips is_regex correctly."""
    classifier = keyword_match_seed.TEST_KEYWORD_CLASSIFIERS[0]

    initial_rows = crud.parse_and_validate_csv(
        _make_csv_bytes(
            "class_name,class_description,musts,nots,is_regex",
            "Regex Class,Desc,(?i)pattern,,true",
            "Normal Class,Desc,keyword,,",
        )
    )
    crud.replace_via_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
        rows=initial_rows,
    )

    csv_export_1 = crud.export_keyword_configs_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )

    exported_rows = crud.parse_and_validate_csv(io.BytesIO(csv_export_1.encode("utf-8")))
    crud.replace_via_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
        rows=exported_rows,
    )

    csv_export_2 = crud.export_keyword_configs_csv(
        session=reseed_tables,
        project_id=classifier.project_id,
        classifier_id=classifier.id,
    )
    assert csv_export_1 == csv_export_2
