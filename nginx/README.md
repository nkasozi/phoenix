# Nginx

This folder contains the nginx configuration and the Dockerfile for an nginx container that can be
used for local development with applications that use header authentiction (`phoenix_superset`). As
it can be used as a reverse proxy that rewrites cookies to headers.

## Usage

The Dockerfile can be used in a `compose.yaml` as such:

```yaml
services:
  nginx:
    build:
      context: ./nginx
      args:
        NGINX_CONF: local_phoenix_superset.conf
    ports:
      - "8081:80"
    links:
      - "my_service:app_service"
```
