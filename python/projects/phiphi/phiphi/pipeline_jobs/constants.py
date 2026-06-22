"""Constants for pipeline jobs."""

GATHER_BATCHES_TABLE_NAME = "gather_batches"
GENERALISED_MESSAGES_TABLE_NAME = "generalised_messages"
DEDUPLICATED_GENERALISED_MESSAGES_TABLE_NAME = "deduped_generalised_messages"
DEDUPLICATED_GENERALISED_AUTHORS_TABLE_NAME = "deduped_generalised_authors"
CLASSIFIED_MESSAGES_TABLE_NAME = "classified_messages"
CLASSIFIED_MESSAGES_ERRORS_TABLE_NAME = "classified_messages_errors"
TABULATED_MESSAGES_TABLE_NAME = "tabulated_messages"
POST_POST_CLASS_CONNECTION_TABLE_NAME = "post_class_connections"
COMMENT_COMMENT_CLASS_CONNECTION_TABLE_NAME = "comment_class_connections"
MANUALLY_CLASSIFIED_AUTHORS_TABLE_NAME = "manually_classified_authors"
CLASSIFIED_AUTHORS_TABLE_NAME = "classified_authors"
DATA_QUALITY_MISSING_AUTHOR_POSTS_TABLE_NAME = "data_quality_post_authors_with_no_posts_on_months"
DATA_QUALITY_ORPHANED_COMMENTS_TABLE_NAME = "data_quality_orphaned_comments"
# The number of items to process from apify in one chunk
DEFAULT_APIFY_SCRAPE_PAGE_SIZE = 1000
# This is the size of a single json object that will be written to gather_batches as a row
# This must be less then 10MB to fit in a BQ row
# 5MB allows for some overhead in the row and easy to compute multiples
# It is the threshold where the row is created so the actual size may be slightly larger
DEFAULT_MAX_MB_BATCH_SIZE = 5
# The max in memory defines how much data the writer will hold in memory before writing to BQ.
# This reduce the number of load jobs to BQ meaning the limits of BQ are less likely to be hit.
# This should bigger than the DEFAULT_MAX_MB_BATCH_SIZE to allow for batching and making it a
# multiple of DEFAULT_MAX_MB_BATCH_SIZE minus 1 will mean it is optimised for batching.
DEFAULT_WRITER_MAX_INMEMORY_MB = 299

# Note DEFAULT_BATCH_OF_BATCHES_SIZE is set via environment variables, see config.py

# Constants for Hugging Face pipelines
# This URI is used in a `EXPORT DATA` statement to export data to GCS, which requires using a "*"
# wildcard. It may result in multiple files being written - consumers should handle this.
HF_INPUT_URI_TEMPLATE = "gs://{bucket}/{prefix}/inputs/job_run_id={job_run_id}/input-*.parquet"
# This URI has a BQ External Table created over it with `job_run_id=*`, so it can be queried as a
# table.
HF_RESULTS_URI_TEMPLATE = "gs://{bucket}/{prefix}/outputs/job_run_id={job_run_id}/scores.parquet"
# This URI is used to store failed rows, which can be used to store failed issues with the hugging
# face classifier.
HF_FAILED_URI_TEMPLATE = "gs://{bucket}/{prefix}/outputs/job_run_id={job_run_id}/failed.parquet"
# HIVE template is the source URI prefix without the wildcard
# https://cloud.google.com/bigquery/docs/external-data-cloud-storage#create-external-table-partitioned
HF_RESULTS_URI_HIVE_TEMPLATE = "gs://{bucket}/{prefix}/outputs/"
HF_EXPORT_OPTIONS = {"format": "PARQUET", "compression": "SNAPPY", "overwrite": True}
HF_FLOW_RESULTS_EXTERNAL_TABLE_NAME = "hf_flow_scores_external_table"
