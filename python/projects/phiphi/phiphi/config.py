"""Configuration of phiphi application."""

import json
import logging
import os
import pathlib
from typing import Any, Optional, Union

import pydantic
from pydantic import networks
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings
from typing_extensions import Annotated

logger = logging.getLogger(__name__)

# Validate sqlite URLs: sqlite://, sqlite+aiosqlite://
SqliteDsn = Annotated[
    MultiHostUrl,
    networks.UrlConstraints(
        host_required=False,
        allowed_schemes=[
            "sqlite",
            # Async
            "sqlite+aiosqlite",
        ],
    ),
]


def parse_cors(input_value: Any) -> list[str] | str:
    """Parse cors origins into a list or str.

    Taken from:
    https://github.com/tiangolo/full-stack-fastapi-template/blob/master/backend/app/core/config.py#L18C1-L23C24
    """
    if isinstance(input_value, str) and not input_value.startswith("["):
        return [i.strip() for i in input_value.split(",")]
    elif isinstance(input_value, list | str):
        return input_value
    raise ValueError(input_value)


def parse_keys(input_value: dict | str) -> Any:
    """Parse keys into a dictionary.

    The keys can be a dictionary or a json string.
    We return type Any as pydantic will validate the type later.
    """
    if isinstance(input_value, dict):
        return input_value
    if isinstance(input_value, str):
        return json.loads(input_value)

    raise ValueError("Environment input value must be a dictionary or a json string.")


class Settings(BaseSettings):
    """Settings of the app taken from environment variables."""

    TITLE: str = "phiphi"
    # This should not be changed and should will be set by the helm chart
    VERSION: str = "0.0.0"

    # Logging
    # This is the logging configuration file use with phiphi.utils.init_logging
    # It has been prefix so not to have a conflict with other python modules that might use the
    # same name.
    PHIPHI_LOG_CONFIG: Optional[str] = None

    # Cors
    # From https://github.com/tiangolo/full-stack-fastapi-template/blob/master/backend/app/core/config.py#L45
    CORS_ORIGINS: Annotated[list[pydantic.AnyUrl] | str, pydantic.BeforeValidator(parse_cors)] = []

    # DB
    SQLALCHEMY_DATABASE_URI: SqliteDsn | pydantic.PostgresDsn
    TESTING_SQLALCHEMY_DATABASE_URI: SqliteDsn | pydantic.PostgresDsn | None = None

    # Seed data
    FIRST_ADMIN_USER_EMAIL: pydantic.EmailStr = "admin@admin.com"
    FIRST_ADMIN_USER_DISPLAY_NAME: str = "admin"
    FIRST_WORKSPACE_SLUG: str = "main"
    FIRST_WORKSPACE_NAME: str = "Main workspace"
    FIRST_WORKSPACE_DESCRIPTION: str = "Main default workspace of phoenix"

    # Authorization
    # This is the header that will be used to get the user email
    # x-auth-request-email is the one set for oauth2-proxy
    HEADER_AUTH_NAME: str = "x-auth-request-email"
    # For Development Use Only!!
    # For cookie AUTH to be active both USE_COOKIE_AUTH and COOKIE_AUTH_NAME must be set
    USE_COOKIE_AUTH: bool = False
    # Name of the cookie that holds the email of the user
    COOKIE_AUTH_NAME: Optional[str] = None
    # For a local cluster to be run without oauth2 implement.
    INCLUDE_INSECURE_AUTH: bool = False
    # Scraping Keys: Top level key is the workspace (main/user_defined) and each subkey is for
    # separate danek APIs (instagram/facebook). Also has the deprecated dict[str,str] type for
    # backwards compatibility
    DANEK_API_TOKENS: Annotated[
        dict[str, Union[dict[str, str], str]], pydantic.BeforeValidator(parse_keys)
    ] = {}
    APIFY_API_KEYS: Annotated[dict[str, str], pydantic.BeforeValidator(parse_keys)] = {}
    # Override the timeout for all Apify Actor runs
    # `timeout_secs` in https://docs.apify.com/api/client/python/reference/class/ActorClient#call
    # Apify timeout default is 3 hours
    # If an actor times out all the results up to that point will be returned.
    APIFY_TIMEOUT_SECS: int = 10800
    # Set the maximum number of seconds a prefect flow waits for an Apify run to finish. After
    # this amount of time, the prefect flow will process all available scraped data from an actor.
    # `wait_secs` in https://docs.apify.com/api/client/python/reference/class/ActorClient#call
    # It is important to set the wait time to be longer then the timeout
    # There has been cases where the timeout is reached but the gather is still running
    # This will cause the gather to not be able to be stopped.
    APIFY_WAIT_SECS: int = 10860
    # This is the amount of time that a flow runner flow will wait for the "inner" flow it is
    # running to finish (in seconds) after which it fails and cancels the "inner" flow.
    # Needs to be longer than the APIFY_WAIT_SECS  plus the time it takes to process that data, so
    # that it can successfully process a timed out apify gather
    INNER_FLOW_TIMEOUT_SECS: int = 14400

    # Pipelines
    # The number of gather batch rows to process in one go during normalisation (reading/writing).
    # To reduce the amount of inserts into BQ we process multiple gather batch rows at once.
    # We have set the default to 5 as with the default max_mb_batch_size of 5MB, as BU has had
    # problems with running large gathers hitting memory limits when running in 2GB machines.
    DEFAULT_BATCH_OF_BATCHES_SIZE: int = 5
    # If True; don't make real Apify calls, read static sample data from within module instead
    USE_MOCK_APIFY: bool = False
    # Danek:
    USE_MOCK_DANEK: bool = False
    # If True; don't make real writes to BigQuery, attempt to use local "eumlator" instead. Note,
    # currently emulation doesn't cover all project BQ queries, as such breaks can occur - use with
    # caution.
    USE_MOCK_BQ: bool = False
    # Root directory for mock BigQuery data, defined relative to this config file, computed by
    # validator function.
    MOCK_BQ_ROOT_DIR: str = "../mock_bq_data"
    # Default location of big query dataset:
    # See docs for options: https://cloud.google.com/bigquery/docs/locations
    # EU is used as default since this means that the data is stored in a GDPR location.
    BQ_DEFAULT_LOCATION: str = "EU"

    # Hugging Face classifier settings
    # This is the name of the flow that is used to run the Hugging Face classifier.
    # Default is the same as defined in
    # python/projects/hugging_face_classifier/prefect.yaml
    HF_FLOW_NAME: str = "inference_classify_flow/phoenix_hugging_face_classifier_inference"
    HF_FLOW_TIMEOUT_SECONDS: int = 86400
    # This can't be optional other wise the project_db migrations will fail.
    HF_GCS_BUCKET_NAME: str = "phoenix-hf-bucket"

    # External services
    PERSPECTIVE_API_KEY: Optional[str] = None
    # https://developers.perspectiveapi.com/s/about-the-api-limits-and-errors
    # The standard Perspective API requests per second quota is 1 per second.
    # This quota can be increased by contacting Perspective API support.
    # 100ms is the aimed for response time from Perspective API requests.
    # If you have been granted a higher quota, you should increase the number of parallel workers,
    # and increase the request limit for period.
    PERSPECTIVE_API_MAX_PARALLEL_WORKERS: int = 1
    # These constants automatically control the max number of requests that are made within the
    # period. Calls over the limit automatically sleep and retry.
    PERSPECTIVE_API_REQUEST_LIMIT_FOR_PERIOD: int = 1
    PERSPECTIVE_API_REQUEST_LIMIT_PERIOD_SECONDS: int = 1

    # Sentry
    SENTRY_DSN: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0
    SENTRY_PROFILES_SAMPLE_RATE: float = 1.0
    SENTRY_ENVIRONMENT: str = "local_development"

    ##### Prefect Results configuration #####
    # These are the prefect settings for persisting results and have to be configured correctly for
    # the API (and flow_runner_flow) to work correctly.
    # See prefect docs: https://docs.prefect.io/3.0/develop/results
    # One note is that this has only been tested with pickle serialisation.
    # They are also used in the prefect_init.py file.
    PREFECT_RESULTS_PERSIST_BY_DEFAULT: bool = False
    PREFECT_DEFAULT_RESULT_STORAGE_BLOCK: Optional[str] = None
    # This will create a prefect storage block on deploy if the storage block is specified.
    # See init_storage_block in prefect_init.py
    CREATE_PREFECT_STORAGE_BLOCK_ON_INIT: bool = True

    ## Mean Costs of gathers per 100k results
    # These are used to calculate the estimated cost of running a gather.
    # The expected cost is calculated as follows:
    # estimated_cost = mean_cost_per_100k_results * (estimated_max_results / 100_000)
    # The key should be ChildTypeName.value of the gather
    MEAN_COST_PER_100K_RESULTS_DICT: dict[str, float] = {
        "apify_facebook_posts": 100.00,
        "apify_facebook_comments": 15.00,
        "apify_facebook_search_posts": 150.00,
        "apify_tiktok_accounts_posts": 50.00,
        "apify_tiktok_comments": 20.00,
        "apify_tiktok_hashtags_posts": 35.00,
        "apify_tiktok_searches_posts": 35.00,
        "apify_x_advanced_searches_posts_comments": 40.00,
        "apify_x_simple_searches_posts_comments": 40.00,
    }
    # allowed % of error margin for running gathers
    GATHER_COST_ESTIMATE_ERROR_MARGIN: float = 0.95
    # Manual upload storage
    # This can be any URL supported by `pandas.to_csv` (eg. gs://, file:///)
    # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html
    MANUAL_UPLOAD_STORAGE_URL: Optional[str] = None
    MAX_MANUAL_UPLOAD_FILE_SIZE: int = 1 * 1024 * 1024 * 1024  # 1GB
    # Concurrency/rate limit settings for big query inserts
    # Due to the limit of concurrent loads into a single table for bigquery it is recommended to
    # have rate limits for number of bigquery writes to each table.
    # Information on the limits of bigquery loads:
    # https://cloud.google.com/bigquery/quotas#standard_tables
    # If this is set to True it will automatically add rate limits for each new projects
    ADD_BIG_QUERY_RATE_LIMITS_ON_PROJECT_CREATION: bool = False
    # If True, provision project resources (BigQuery dataset, Superset dashboard) on project
    # creation. When True with USE_MOCK_BQ=False, resources are provisioned via a background
    # Prefect flow. When False, no external resources are created (useful for testing).
    PROVISION_PROJECT_RESOURCES_ON_PROJECT_CREATE: bool = True
    # Danek costs configuration:
    # These are the agreed costs per request for each gather type.
    # They are used to compute the costs as the Danek API does not provide costs.
    DANEK_COST_PER_100K_RESULTS_DICT: dict[str, float] = {
        "danek_facebook_searches_posts": 120.00,
        # Both these use the same cost:
        # 0.5 per 1000 requests
        # around 10 posts/comments per request
        # Number of requests per 100k results = 100_000 / 10 = 10_000 requests
        # Cost per request = 0.5 / 1000 = 0.0005
        # Cost per 100k results = 10_000 * 0.0005 = 5.00
        "danek_instagram_posts": 5,
        "danek_instagram_comments": 5,
    }
    # Keyword match classifier settings
    # Maximum number of keywords per BigQuery query batch to avoid query complexity limits
    KEYWORD_MATCH_KEYWORDS_PER_BATCH: int = 100

    ## Hugging Face
    # Whitelist of Hugging Face models that are allowed to be used in the application with no
    # validation.
    HUGGING_FACE_MODELS_WHITELIST: list[str] = [
        # Has no safe tensors file, but is whitelisted because is legitimate organisation.
        "Hate-speech-CNERG/dehatebert-mono-arabic",
        # Has no safe tensors file, but is whitelisted because is legitimate organisation.
        "worldbank/naija-xlm-twitter-base-hate",
        # Has no safe tensors file, but is whitelisted because is legitimate organisation.
        # Added for Request by Allan (Build Up)
        "mradermacher/DeepSeek-R1-Bengali-Hate-Speech-Classification-Multi-Class-merged-GGUF",
        "DeadBeast/mbert-base-cased-finetuned-bengali-fakenews",
        "shukdevdattaEX/DeepSeek-R1-Bengali-Hate-Speech-Classification-Multi-Class",
    ]

    # Superset Integration
    # Enable/disable Superset dashboard provisioning
    SUPERSET_PROVISIONING_ENABLED: bool = True
    # Internal API URL for Superset (used by phiphi pods)
    SUPERSET_API_URL: str | None = None
    # External URL for user-facing dashboard links
    SUPERSET_EXTERNAL_URL: str = ""
    # Service account email for X-Auth-Request-Email header (defaults to FIRST_ADMIN_USER_EMAIL)
    SUPERSET_SERVICE_ACCOUNT_EMAIL: str = "admin@admin.com"
    # UUID of the shared BigQuery database connection in Superset
    # If the UUID exists on Superset at the time of provisioning, it will be used,
    # and the databases folder in the standard_v1 template will be ignored
    # If not, the Superset connection in the databases folder will be used
    # This is as a result of how Superset handles Dashboard imports
    SUPERSET_DATABASE_UUID: str = ""
    # URI of the shared BigQuery catalog / project in Superset
    # You will find it in the export of the manually added database connection in Superset.
    # This is referenced in the Dashboard provisioning process
    # It overrides the catalog: key in the datasets folder of the standard_v1 template
    # Necessary for Idempotent provisioning across environments (dev or prod)
    SUPERSET_DATABASE_SQLALCHEMY_URI: str = ""

    def model_post_init(self, __context):  # type: ignore[no-untyped-def]
        """Set the mock bq root directory as an absolute path."""
        path = pathlib.Path(self.MOCK_BQ_ROOT_DIR)
        if not path.is_absolute():
            config_file_dir = pathlib.Path(__file__).parent
            self.MOCK_BQ_ROOT_DIR = str(config_file_dir.joinpath(path).resolve())
        self.MOCK_BQ_ROOT_DIR = str(path)


if os.environ.get("SETTINGS_ENV_FILE"):
    logger.warning(
        f"Using settings file: {os.environ.get('SETTINGS_ENV_FILE')}."
        " Be aware that environment variables will take priority over variables defined in the"
        " settings file."
        " IE. `export TITLE='title_env'` will override the TITLE='title_file' variable in the"
        " settings file."
    )
    settings = Settings(_env_file=os.environ.get("SETTINGS_ENV_FILE"))  # type: ignore [call-arg]
else:
    settings = Settings()  # type: ignore [call-arg]
