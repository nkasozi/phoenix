# PhiPhi

This project is the main API and backend processing for phoenix.

## Usage

See:
* [Getting started with Pipeline Jobs](./docs/getting_started_with_pipeline_jobs.md) for
  information on how to use the pipeline jobs.

## Development

For simplicity `phiphi` uses a docker compose environment rather then a local virtual environment.
This is so as the project gets more complex the CI and development environment are the same and we
are not maintaining two different environments. It is still recommend to set up an virtual
environment using the instructions in the [`/python/README.md`](/python/README.md) so that your IDE
can provide better support.

To start the development environment run the following command:
```bash
make up
```

Visit the API at [`http://localhost:8080/`](http://localhost:8080/) and the docs at
[`http://localhost:8080/docs/`](http://localhost:8080/docs/). By default you should be able to
change the user by setting the cookie `phiphi-user-email` to the email of the user you want to use.

In the Swagger UI (`/docs`), you can authenticate by clicking the "Authorize" button and entering
your email (e.g. `admin@admin.com`) in the **APIKeyHeader (apiKey)** field. This sets the
`x-auth-request-email` header on all requests made through the UI.

See the [`Makefile`](Makefile) for more commands.

### Running Commands in the Development Environment

You can run scripts and basic Python commands within the development container. First, start the
development environment. Then, in a new terminal, run:

```bash
make bash_in_api
cd project/phiphi/
```

You can now execute commands such as:

```bash
python -m ...
```

### Testing and Linting

Make commands to run testing and linting:
```bash
make all
make test
make format
```

Be aware that these commands use the `make` in the parent directory, but inside the container. This
is to ensure that the commands are run in the same environment as the API and to simplify the setup
of the development environment.

### GCP Setup

For development and usage of PhiPhi, a GCP project and local environment authenticated with
`gcloud` are required. Authenticate locally by running:

```bash
gcloud auth application-default login
```

Set your active GCP project with:

```bash
gcloud config set project <project_id>
```

See [docs/gcp_setup.md](docs/gcp_setup.md) for required permissions in a project.

### Integration Tests

Integration tests allow for faster development iterations. Before running these tests, ensure your
GCP credentials are correctly configured (see [GCP Setup](#gcp-setup)).

Run the integration tests using:

```bash
make integration_test
```

Be aware that the integration tests will create and delete resources in the Gcloud project. Make
sure that you are using the correct project. Also be aware that if the integration test fails, the
resources might not be deleted and will need to be deleted manually. See documentation in the test
file for more information.

## Problems with files created in the container

If a file is created in the container, for instance using `make alembic_revision`, it could have a
different owner then your default shell user. To fix the local permissions if a file is created in
the container, run. This command will ask for you password:
```bash
make fix_local_permissions
```

It is also possible to run the commands in the container as the current user. For Unix systems
you can you can run the following before running a `make` or `docker compose` command:
```bash
source set_host_uid_unix.sh
```

## Databases

In phiphi there are two types of database:
- platform: This is the main database for the user platform. It contains contains
configurations for users, workspaces, and projects. There is a single test and single
production Postgres database.
- project: There is a separate database for every project. This contains the scraped
and processed data for the project. There are as many project DBs as there are
projects, plus more testing and development. Bigquery is used for project databases in
production, and a mixture of sqlite and bigquery is used for testing and development.

Both databases are managed by alembic and use SQLAlchemy to define the tables/ORM models.

### Connecting to the development database

To connect to the platform database while the development environment is running:

```bash
# Via docker compose exec
docker compose exec postgres psql -U postgres -d dev_db

# Or direct connection
psql -h localhost -p 5432 -U postgres -d dev_db
# Password: password
```

Connection details:
- Host: `localhost`
- Port: `5432` (dev) / `5433` (test)
- User: `postgres`
- Password: `password`
- Database: `dev_db` (dev) / `test_db` (test)

### Platform database migration

If you have created a new file with a new model, you will need to add this to
`phiphi/all_platform_models.py` so that alembic has it in the table metadata.

Use make commands to create a revision. Be aware that by default the revision will be created with
the user `root`. See "Problems with files created in the container" for more information.
WARNING: The revision description must not contain spaces. (The commands get messed up, so use _.)
```bash
message="<revision description>" make alembic_revision
```

This will create a new migration file in the `phiphi/migrations/versions/platform` directory. The
file will be `r_$datetime_$revision_slug_$description`.

Check and edit the migration file as needed and fixing any linting issues.

The migrations will be applied when you do `make up` and the `api` service is started. However, if
you want to explicitly run migrations you can do:
```bash
make alembic_upgrade
```

Note: When we have the use case to add another alembic branch this should be done making an
addition to `version_locations` in `alembic.ini` separating new additions with the
`version_path_separator`.

See the `Makefile` for more commands.

### Project database migration

For project data migrations an sqlite database is used for testing. For production the migrations
are applied to a bigquery dataset that is specific to a project. See the file
[`project_db.alembic.ini`](./project_db.alembic.ini) `sqlalchemy.url` for more information about
test migration db.

To create and test new tables and their migrations:

A `sqlalchemy.Table` should be create and not an `ORM` model. See docstring in
[phiphi/project_db.py](phiphi/project_db.py) for more information for gottchas and best practices.

Create new tables in a new file and add it as an import to `phiphi/all_project_tables.py`.

Upgrade the test migration db: `make project_alembic_upgrade`.

Use make commands to create a revision/file with migration. Be aware that by default the revision
will be created with the user `root`. See "Problems with files created in the container" for more
information.
WARNING: The revision description must not contain spaces. (The commands get messed up, so use _.)
```bash
message="<revision description>" make project_alembic_revision
```

This will create a new migration file in the `phiphi/project_db_migrations/versions/project`
directory. The file will be `r_$datetime_$revision_slug_$description`.

Check and edit the migration file as needed and fixing any linting issues.

Apply the migration to the test database: `make project_alembic_upgrade` to see if it works.

If you want to manually test this in a real cloud dataset:
* Set up you gcloud credentials: `gcloud auth application-default login`
* Create a dataset in BigQuery
* In the file project_db.alembic.ini set sqlalchemy.url to the dataset:
  `bigquery://<project_id>/<dataset_id>`
* Run `make project_alembic_upgrade`. The google credentials should be automagically set up in the
  container.
* Check the dataset in BigQuery to see if the tables were created
* Delete the dataset in BigQuery
* Change the sqlalchemy.url back to the test sqlite database

## Running Deployments Locally for Testing Full Flow Runs

When developing flows, you might want to test the full flow execution locally. This can be done
using the local cluster. For more details on setting up and using the local cluster, refer to the
`phoenix` root `README`.

The console will automatically start the necessary deployments as needed. You can also access the
local Prefect server to monitor and manage your flows; see the root `README` for instructions on
how to view the local Prefect server.

Additionally, if you wish to run a flow with a debugger, see the [Debugging Flows
Locally](./docs/debugging_flows_locally.md) guide for more information.

## Adding a new gather

See the [Adding Gathers](./docs/adding_gathers.md) document for more information.

### Danek gathers

Danek gathers use scrapers build by jandanecki@danek.tech. Contact him for access to the scrapers.
