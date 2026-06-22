# Adding Gathers to Phiphi

This document outlines the steps to add a new gather type to Phiphi.

When adding a new gather it is recommended to follow the steps outlined here while using one of the
other gathers, such as
[`apify_facebook_posts`](python/projects/phiphi/phiphi/api/projects/gathers/apify_facebook_posts/),
as a example for the changes and conventions.

Currently there are Apify and Danek gathers, but in the future there might be other gather types.
These steps are then specific to Apify and Danek gathers.

Apify gathers are built on top of Apify actors: https://apify.com/store/categories

Danek gathers are built on top of a custom API that is built by Jan Danecki: jandanecki@danek.tech

## Steps - Stage 1

### Decide which Apify actor or Danek API to use

Look at the possible actors here: https://apify.com/store/categories

Or contact Danek about a possible scraper, if you are adding a Danek gather you may need to add
code to integrate with a new API. This is not documented here but look at the file
[`danek/facebook_search_scraper.py`](python/projects/phiphi/phiphi/pipeline_jobs/gathers/danek/facebook_search_scraper.py)
for examples.

### Decide on a `child_type_name`

This name should follow the conventions of the other child gather names. However, since there are
lots of different types of actors and scrapers please feel free to come up with a name that make
sense and possibly breaks the naming convention of child gathers. This name can be discussed with
others in the MR.

Make the additions:
- Add the `child_type_name` to `ChildTypeName` in `phiphi/api/projects/gathers/schemas.py`.
- Add a folder `phiphi/api/projects/gathers/<child_type_name>/` with an `__init__.py` file.

### Make base schemas

Make schemas in `phiphi/api/projects/gathers/<child_type_name>/schemas.py` for the
`<child_type_name>Base` and `<child_type_name>Response`. For class names use `CamelCase` and
for the fields use `snake_case`. The `<child_type_name>Response` schema should inherit from the
`GatherChildResponseBase` schema.

These schemas should use attribute names that are clear to a technical peace builder. They can be
different from the names that are used in the Apify actor or a scraper. If they are then use the
Pydantic Field parameter `serialization_alias` to map the Apify attribute name. For Danek we
generally don't use `serialization_alias` as attributes are often changed in to a different format
with python code for the API.

If needed add test for the serialization of the Response schema in
`phiphi/tests/api/projects/gathers/test_<child_type_name>_schemas.py`. See other examples for more
information.

Add the import of the schemas to the `__init__.py` file in the folder for the new gather type. See
other `__init__.py` of other child gathers for examples.

### Add `job_run_resource_estimate` to `<child_type_name>Response`

The `job_run_resource_estimate` field should be integrated into the `<child_type_name>Response`
schema. This field plays a critical role in estimating the resource consumption of a gather
operation when it is executed. Such estimates act as safeguards, minimizing the risk of a gather
exceeding resource limits.

Currently, for Apify gathers the resource estimation is handled by a `job_run_resource_estimate`
instance method on the Response class, which leverages values in the
`MEAN_COST_PER_100K_RESULTS_DICT` to calculate the expected cost based on the maximum estimated
results. A value for you gather should be added to this dict, within `phiphi/config.py`.

To ensure accurate estimations, it is essential that all gathers include limiting attributes, as
these attributes are vital for the estimation process. Examples are `limit_posts_per_search`.
See the other Apify gathers for more information.

For Danek gathers the cost is mostly based on the number of results returned from the API.
`DANEK_COST_PER_100K_RESULTS_DICT` is used to calculate the expected cost based on the maximum
estimated results. See other Danek gathers for more information.

### Make an MR

At this point it is recommended to make a merge request to the `phiphi` repository. This will allow
for feedback and discussion on the `child_type_name` and what is being proposed to be added.

## Steps - Stage 2

### Add schemas to child_types.py`

Add the `Base` and `Response` schemas and `child_type_name` to the config maps in
`phiphi/api/projects/gathers/child_type.py`. This includes making the correct additions to
the variables `AllChildTypesUnion`, `CHILD_TYPES_MAP` and `CHILD_TYPES_MAP_PROJECT_DB_DEFAULTS`.

Add `child_type_name` to `gather_apify_actor_map` in
`python/projects/phiphi/phiphi/pipeline_jobs/gathers/apify/scrape.py`.

### Make an example gather

Add an example gather in `phiphi/tests/pipeline_jobs/gathers/example_gathers.py`. Do not use PI
data in the definition but it is recommended to use attributes that actually return results from
Apify as this will be used to make a real request to Apify.

### Make a real request

#### Apify

Using the example gather you made in the previous step, make a real request to the gather service to
get real output data for the example gather. This can be done by running the integration tests with
`phiphi/tests/pipeline_jobs/gathers/test_apify_scrape.py::manual_test_apify_scrape_and_batch_download`.
Don't forget to read the test docstring and change the test to use the correct example gather.
Using this test will mean that you will also test the batch download functionality for the gather
you are adding.

#### Danek

When adding the Danek integration code it is recommended to create an integration test like the file
[danek/test_facebook_search_scraper.py](python/projects/phiphi/phiphi/tests/integration/danek/test_facebook_search_scraper.py).
This can be used to make a real request to the Danek API and get the real output data for the
example gather results.

### Create sample data

Add an anonymised (no PPI) version of the real output data that you received from the request as
the json sample data.
- For apify these are stored in: python/projects/phiphi/phiphi/pipeline_jobs/gathers/apify/sample_data
- For danek these are stored in: python/projects/phiphi/phiphi/pipeline_jobs/gathers/danek/sample_data

Add the new sample raw data to switch in `phiphi/pipeline_jobs/gathers/utils.py`.

It is important to remove PI data. List of things that should be removed:
- Ids
- Ids or usernames of accounts
- People's names or usernames in the text of a post or comment
- URLs

One option is to replace this with the attribute name and an index. e.g.
tiktok-hashtags-authorMetaId1 for an author's id. See tiktok_hashtags_posts.json for more
examples.

### Add normalizer

Add normaliser to `phiphi/pipeline_jobs/gathers/normalisers.py` including tests and fixtures to
`phiphi/tests/pipeline_jobs/gathers/conftest.py`

Also add the normaliser to the variable `gather_normalisation_map` in
`phiphi/pipeline_jobs/gathers/normalise.py`.

### Make an MR

At this point the gather should work through the pipeline. This has been tested with the use of
`manual_test_apify_scrape_and_download` or an integration test to create the sample data and
normaliser test that you did in the previous steps. If you want you can also run the local cluster
and then run a `gather_flow` through the prefect server (http://localhost:4200) with the correct
parameters to see that the gather runs successfully.

It is a good idea to make a MR so others can see the changes and give feedback.

## Steps - Stage 3

### Add ORM models and migrations

Add the ORM models to `api/projects/gathers/<child_type_name>/models.py`. Create the alembic
migration following the docs in `phiphi/README.md`. You will need to import the models in
`phiphi/all_platform_models.py`.

### Add the schemas for Create and Update

For the create (POST) and update (PUT) routes, see "Add child routes" below, that will create and
update the gather in the platform database you will need to add schemas for these routes. They
define the allowed fields and types for the request body of the API routes. These schemas should be
similar to the `Base` schema but should have the fields that are required for the creation and
update of the gather. For instance the update schema should have all attributes of the schema be
optional. See the `apify_facebook_posts` example for more information and conventions.

Add the schemas for `<child_type_name>Create` and `<child_type_name>Update` to
`api/projects/gathers/<child_type_name>/schemas.py`.

### Add a seed

For testing Phiphi creates test data in the platform database. This test data is called a seed and
this seed data will automatically be added to the db when using the local cluster and for tests
that use the fixture `reseed_tables`. To add a seed you will need to create a seed file and then
call that seed functionality in the entry point `phiphi/seed/main.py`.

Add a seed file `phiphi/seed/<child_type_name>_gather.py` that has a function that creates a gather
of the type you are adding. Add the call of the seed function to `phiphi/seed/main.py`. You may
need need to update other tests like the `test_get_gathers` which asserts the number of gathers in
the database.

### Add child routes

To have the console UI and the admin UI able to create and update the gathers of the new type
you will need to add routes to the API. In Phiphi these routes are called child routes because they
are the child gather API routes. Adding the child routes will allow the UI to make the correct http
requests to the API to create and update the gathers. These child routes can be added automagically
if you follow the conventions of adding correct config to the `child_routes.py` file.

Add schemas for the gather type to the variable `list_of_child_gather_routes` in
`phiphi/api/projects/gathers/child_routes.py` to create the child routes.

It is a good idea to also add some tests for the routes. Add the tests for create and update routes
to `phiphi/tests/api/gathers/test_<child_type_name>.py`

### Run a full check on local cluster

To run the cluster see `README.md`. Then runs checks:
- create the gather of the new type from the API docs `http://api.phoenix.local/docs`
- run the gather of the new type by making a `POST` to `job_runs` with the correct gather id and
  gather type
- check that the gather run completes successfully. Check that the `GET` `gather` for that
  gather has the correct status and that the flows in prefect server `http://localhost:4200` are
  completed successfully.
- Check that the output data was correct in the BigQuery project that the local cluster is connected
  to. It should use the sample data that was added in the previous steps.

### Make an MR

This is the final MR for the functionality for Phiphi.

## Steps - Stage 4

Add Console UI additions, see `console_ui/README.md`.
