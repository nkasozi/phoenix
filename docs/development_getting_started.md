# Development Getting Started

Welcome to the development guide for contributors! This document outlines the steps necessary to
set up your development environment for working on the project. Our project leverages a local
Kubernetes (k8s) cluster for the development of the full system, while sub-projects may have
smaller-scale set-ups for more focused development.

This approach allows you to test changes in a controlled environment that closely mimics
production. For sub-projects, smaller-scale set-ups are available and can be used for more specific
development tasks. See sub folders for more information on this.

Thank you for contributing to our project, and happy coding!

## Using `asdf` for Version Management

We use `asdf` as our tool of choice for managing multiple runtime versions for different languages
and tools. `asdf` allows you to easily switch between different versions of tools like Node.js,
helm, Python, and more, ensuring consistency across our development environments.

You can also use a different version management system and see
[.tool-versions](./../.tool-versions) for the configuration of versions.

Install `asdf`: Follow the instructions on the `asdf`, see
[docs](https://asdf-vm.com/guide/getting-started.html)

To setup `asdf` with the correct plugins and  versions of the tools, run the following command:

```bash
make setup_asdf
```

This will also install `kubectl` that is needed for working with the local cluster.

## Set up a local cluster

We recommend that you use [mircok8s](https://microk8s.io/) but you can use any as documented by
tilt, see below. To get up and running follow the steps:

1. [Install mircok8s](https://microk8s.io/docs/install-alternatives)
3. Check that you don't have anything else running on port 80 of your local machine
4. Run `source setup_microk8s.sh` to set up the cluster and `kubectl`
5. The command will output instructions on setting up your `/etc/hosts` file

On non linux systems we have had problems with the ingress of microk8s and are still working on a
solution.

### Using another local cluster

If is possible to use a different cluster
that tilt works with, see [tilt docs on clusters](https://docs.tilt.dev/choosing_clusters).

If you do this the set up of the ingress/host name and the `kubctl` setup might be different. For
instance when using `k3s` you will need to add `<traefik-serivce-ip> phoenix.local` to your
`/etc/hosts` and [follow cluster access](https://docs.k3s.io/cluster-access)

## Setting secrets for local cluster

There are no secrets needed for the default local cluster but other clusters need secrets to be
set. If you are using the prefect-worker you will need to set the secrets for this.

## Running the Development Environment with tilt up

Our development environment leverages [`tilt`](https://tilt.dev/) to streamline the process of
running services in the local Kubernetes cluster.

Once you have you local cluster up and running you can do:

```bash
make up
```

In the browser you will be able to see the `tilt` UI via the URL that `tilt up` prints.

You can also use the `tilt` cli if needs be. Such as `tilt down` to bring down the resources in the
cluster.

You can also use `make clean` to remove all the tilt resources and default volumes in the cluster.

## Authentication

The default local cluster uses the insecure authentication via the api and does not require any
setup.

## GCP Requirements

To run the platform locally, you'll need a GCP project and a service account with appropriate
permissions. Refer to [`docs/gcp_setup.md`](docs/gcp_setup.md) for detailed instructions on
configuring GCP.

Once you obtain the service account key, add it to the `local/secrets.yaml` file as
`gcp_service_account.json`. For additional details and examples, see
[`charts/main/example_secrets.yaml`](charts/main/example_secrets.yaml).

## Prefect server and deployments

By default the local cluster will create a prefect server and prefect worker.
* You can visit
`http://localhost:4200` and you will see the prefect server dashboard.
* You should be able to see the status of the health-check flow in the logs of the
  prefect-deployment pod (in the tilt ui).
* If you make a change to the code and you notice your changes are not in the flows you may need to
  click on the "reload" button to rebuild the `prefect-deployments` resource in the tilt UI.

## Local cluster with authentication and SSL

See [cluster/local_with_auth/README.md](cluster/local_with_auth/README.md) for a local cluster with
authentication and SSL. This is useful for testing the full system with authentication and SSL.

## Hello world

Once your set up is complete you should be able to see an hello world at. Beaware you will need to
log in to the configured authentication provider.

* [http://console.phoenix.local/](http://console.phoenix.local/)
* [http://api.phoenix.local/](http://api.phoenix.local/)
* [http://dashboard.main.phoenix.local/](http://dashboard.main.phoenix.local/)

## Dev cluster in the cloud

It is possible have a development cluster in the cloud. This is useful for testing the deployment
process and for testing the system in a more production like environment.

First you will need to create a cluster. We used EKS but gcloud might be better.

You will then need to create a `.dev.env` that does the following:
- define a `KUBE_DEV_CONTEXT` variable of the context of the cluster
- define a `DEV_NAMESPACE` variable of the namespace to use
- define a `DEV_BASE_HOST` variable of the base host name to use
- if needs be update the kube config with the cloud context.

See `.example_aws.dev.env` for how we did this with EKS.

Then run:
```bash
source setup_dev.sh
make dev_up
```

To clean up the resources including `pvcs` run `make dev_clean`.

## Local cluster troubleshooting

We are still looking for solutions to these problems:
- ingress not working on mac for microk8s
- Authentication 401 errors on all API requests: microk8s v1.32+ ships Traefik as its default
  ingress controller instead of nginx. The helm chart was originally designed for nginx
  (dev/prod clusters still use nginx) and uses `nginx.ingress.kubernetes.io/` annotations for
  forward auth. To maintain backward compatibility with existing nginx clusters while supporting
  Traefik locally, the chart has a `traefik_ingress` flag. When set to `true` (already the case
  in `clusters/local/values.yaml`), a Traefik `Middleware` CRD is deployed for forward auth in
  addition to the existing nginx annotations — nginx clusters continue to use the nginx
  annotations and ignore the Traefik ones, and vice versa. If you see 401 errors, confirm
  `traefik_ingress: true` is set in your local values.
- running the postgresql bitnami image on MACs on apple silicon / arm64 architecture:
-- A quick solution is to change the `superset.postgresql.image.image` to `postgres` and
`superset.postgresql.image.tag` to something like `16.2` in the `charts/local/values.yaml` file.
- If you get "Unable to connect to the server: x509: certificate is valid for <internal IPs>, not
  <external IP>" in the logs of all pods:
```bash
sudo microk8s refresh-certs -e ca.crt
rm ~/.kube/microk8s-config
source setup_microk8s.sh
```
