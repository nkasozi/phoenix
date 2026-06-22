# Superset Integration Tests

## Prerequisites

1. **Start the phiphi development environment** (creates the shared Docker network):
   ```bash
   cd python/projects/phiphi
   make up
   ```

2. **Start the phoenix_superset service**:
    - Look at the README.md in the `phoenix_superset` project for instructions on how to set up the
      service.



3. **Create a "Google BigQuery Dev" database connection in Superset**:
   - Check the superset docs for how to login to the local Superset instance
     (http://localhost:8089). `cat python/projects/phoenix_superset/README.md` for instructions.
   - Create a new database connection named "Google BigQuery Dev"

4. **Get the database UUID**:
   - Export the database from Superset
   - Look in the exported file at `databases/Google_BigQuery_Dev.yaml`
   - Copy the UUID value

5. **Configure the environment**:
   - Edit `python/projects/phiphi/docker_env.dev`
   - Set the UUID:
     ```
     SUPERSET_DATABASE_UUID=<your-uuid-here>
     ```
   - Set the URI:
     ```
     SUPERSET_DATABASE_SQLALCHEMY_URI=<your-uri-here>
     ```
     > ℹ️: You need this to see the data in the Superset UI.
     >
     > - Should be of format: `bigquery://<concerned-bq-project>/`
     > - You will find it in the export of the manually added database connection in Superset.
     >   - Key: `sqlalchemy_uri`

6. **Restart the phiphi Docker container** to pick up the new environment variables:
   ```bash
   cd python/projects/phiphi
   make down
   make up
   ```

## Running the Tests

```bash
make bash_in_api
pytest projects/phiphi/phiphi/tests/integration/superset/
```
