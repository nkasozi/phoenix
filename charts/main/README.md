# Phoenix Helm Chart (Main)

This is the main Helm chart for Phoenix, used to deploy the Phoenix platform in a Kubernetes
cluster.

The chart’s default values are defined in the [`values.yaml`](charts/main/values.yaml) file. For
example cluster-specific overrides, see the files in the [`clusters/`](clusters/) directory.

## Secrets

Currently secrets for the chart are not stored in the chart. The expectations is that Secret
resource should be created in the cluster. The secrets should be created in the namespace that the
chart is deployed in.

See the [example_secrets.yaml](example_secrets.yaml) for the secrets that are expected.


## SSL Certificates

The chart uses [cert-manager](https://cert-manager.io/docs/) for SSL certification creation. It is
disabled by default.

Although this chart contains a cert-manager as a subchart it is not enabled by default. This is
recommended that you DO NOT install the cert-manager as a subchart. Instead you should install
cert-manager as a separate helm chart. See [cert-manager
docs](https://cert-manager.io/docs/installation/helm/).

To set up the certifications for a deployment:

* Release the chart with the `cert-manager.enabled` and `cert_issuer.enabled` set to `false`
* Set up the dns records for the domain so that the domain points to the load balancer/ingress
* ONLY if for testing: Enable cert-manager `cert-manager.enabled` and install
* Once the cert-manager is installed set the `cert_issuer.enabled` to `true` and other values in
  `cert_issuer`. See the [values.yaml](values.yaml) for the options.
* Set the `cert_issuer.issuer_name` to the name of the issuer `letsencrypt-staging`
* Check that the certificates are created and "READY" by running `kubectl get certificates -A`
* If they are ready you can use `cert_config.issuer_name` to `letsencrypt-prod` to get the production
  certificates
* You can then visit the https://<domain> and see the certificates are valid

## Authentication

The chart uses [oauth2-proxy](https://oauth2-proxy.github.io/oauth2-proxy/) for authentication. It
can be configured to use a variety of authentication providers.

Be aware that the configuration of the cookie can be some what complex. For instance:
- http-only cookies can not be seen by javascript. This needs to be false to use
  `console.env_auth_cookie= "_oauth2_proxy"`
- secure means that the cookie can only be sent over https
- same-site "strict" and "lax" cookies can mean that a console on a different domain will not have
  the cookies
- same-site "none" cookies can be used for cross-site cookies but require the secure flag to be set
  on the cookie

### Insecure authentication for local testing

The chart can be configured to use an insecure authentication. This is useful for testing and
should not be used for production. See the [./values.yaml](./values.yaml) for the options.

## CORS

Their are a number of complexities with CORS. In that for the console to work the CORS for the
ingress (oauth and general) and the API need to be set up so that the site URL that the console is
served from is an allowed origin for the ingress and the API. Be careful to use the correct schema
(http|https). See [./values.yaml](./values.yaml) for the options.

## Prefect integration

Phoenix heavily relies on prefect to process data and orchestrate long running jobs. This chart has
the possibility to use the cloud prefect or a self hosted prefect server. This uses the prefect
charts to do this
[prefect-server](https://github.com/PrefectHQ/prefect-helm/tree/main/charts/prefect-server) and
[prefect-worker](https://github.com/PrefectHQ/prefect-helm/tree/main/charts/prefect-worker). There
are different configuration options for the prefect server and the cloud see documentation on the
charts to correctly configure the prefect server and the prefect worker.

Be aware that the baseJobTemplate for the work pool will be created and update by this chart in the
configured prefect server.

### Prefect Server Ingress

The chart can expose the Prefect server UI externally with role-based authentication. This allows
you to restrict access to users with specific roles (e.g., `admin`).

See [docs/prefect_ingress_setup.md](../../docs/prefect_ingress_setup.md) for the full setup guide,
including an Auth0 example.

## Shared Redis

The chart includes an optional shared Redis service that can be used by Superset and Prefect,
replacing their embedded Redis instances.

### Enabling Redis

Set `redis.enabled: true` in your values. See the `redis` section in
[values.yaml](values.yaml) for all configuration options.

### Configuration Patterns

**Helm-managed Secret (Development):**
```yaml
redis:
  enabled: true
  auth:
    password: "dev-password"
```

**Existing Secret (Production):**
```yaml
redis:
  enabled: true
  auth:
    existingSecret: "redis-credentials"
    existingSecretKey: "password"
```

**Managed Redis (AWS ElastiCache):**
```yaml
redis:
  enabled: true
  useManaged: true
  managedUrl: "rediss://:AUTH_TOKEN@your-cluster.cache.amazonaws.com:6379"
```

When enabled, Superset automatically uses the shared Redis for caching and Celery.

## GCP Setup

To use the chart, you must have a GCP project and a service account with the appropriate
permissions.  Refer to [docs/gcp_setup.md](docs/gcp_setup.md) for detailed setup instructions.
