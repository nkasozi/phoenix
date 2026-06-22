# GCP Setup for Phoenix

To use Phoenix or PhiPhi in any environment—including local clusters, PhiPhi standalone, or
production—you must configure a Google Cloud Platform (GCP) project and a service account with
appropriate permissions.

## GCP Project Creation

Create a GCP project using either the GCP Console or the `gcloud` CLI. For detailed instructions,
refer to the [Google Cloud
Documentation](https://cloud.google.com/resource-manager/docs/creating-managing-projects).

## GCP Configuration for PhiPhi Standalone

If you're developing exclusively with PhiPhi, you can set up your local `gcloud` authentication,
which will be used for local development. Refer to
[`python/projects/phiphi/README.md`](python/projects/phiphi/README.md) for detailed instructions.

For additional deployment scenarios, please refer to the sections below.

## GCP Service Account

Create a service account with the necessary permissions using either the GCP Console or the
`gcloud` CLI. Refer to the [Google Cloud Service Accounts
Documentation](https://cloud.google.com/iam/docs/creating-managing-service-accounts) for detailed
instructions.

Ensure your service account has the following roles:

- `roles/bigquery.dataEditor`
- `roles/bigquery.jobUser`
- `roles/bigquery.metadataViewer`
- `roles/bigquery.readSessionUser`
- `roles/storage.insightsCollectorService`

## GCP Service Account Key

Generate a key for your service account through the GCP Console or using the `gcloud` CLI.

Once generated, this key must be included in your chart secrets. See the following files for
further guidance:

- `charts/main/example_secrets.yaml`
- `charts/main/values.yaml`
