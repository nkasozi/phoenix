"""Test classifiers crud."""

from phiphi.api.projects.classifiers import base_schemas, crud


def test_get_pipeline_classifiers(reseed_tables):
    """Test get pipeline classifiers."""
    classifiers = crud.get_pipeline_classifiers(reseed_tables, 1)
    # Using greater than or equal to so that this doesn't need to be updated with every additional
    # classifier to the seeds.
    assert len(classifiers) >= 6
    assert classifiers[0].id == 3
    assert classifiers[1].id == 4
    assert classifiers[2].id == 5
    assert classifiers[3].id == 8
    assert classifiers[4].id == 9
    assert classifiers[5].id == 10
    for classifier in classifiers:
        assert classifier.type not in base_schemas.SINGLE_RUN_CLASSIFIER_TYPES

    # Currently project 2 is the only project with manual_post_authors classifiers
    non_single_run_classifiers = crud.get_pipeline_classifiers(reseed_tables, 2)
    all_classifiers = crud.get_pipeline_classifiers(
        reseed_tables, 2, include_single_run_classifiers=True
    )
    # There should be more classifiers when including single run classifiers
    assert len(all_classifiers) > len(non_single_run_classifiers)


def test_get_pipeline_classifier(reseed_tables):
    """Test get pipeline classifier."""
    classifier = crud.get_pipeline_classifier(reseed_tables, 1, 3)
    assert classifier
    assert classifier.id == 3

    # classifier 1 has no version
    classifier = crud.get_pipeline_classifier(reseed_tables, 1, 1)
    assert classifier is None

    # classifier 2 is archived
    classifier = crud.get_pipeline_classifier(reseed_tables, 1, 2)
    assert classifier is None
