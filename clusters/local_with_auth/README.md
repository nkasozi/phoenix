# Local with authentication 

This local cluster will set up the phoenix platform with:
- autentication to the dev buildup auth0 authentication app
- ssl with self signed certificates

## Running
It can be run with:
```
source setup_microk8s.sh
make local_with_auth_up
```

You will need to:
- follow the instructions to set up your `/etc/hosts` file
- set up the secrets in `cluster/local_with_auth/secrets.yaml` file to include the auth0 client id
  and secret. See below for more information on this.

You will then need to visit the following urls and proceed with the insecure certificate. Be aware
the you may need to log in at some point:
- [https://oauth.phoenix.local/](https://oauth.phoenix.local/)
- [https://api.phoenix.local/](https://api.phoenix.local/)
- [https://console.phoenix.local/](https://console.phoenix.local/)

## Authentication set up

By default `make local_with_auth_up` cluster uses the auth0 build up dev authentication app. The
client id and secret are set in the `cluster/local_with_auth/secrets.yaml` file. These secrets can
be found in the auth0 buildup dev app settings,
[here](https://manage.auth0.com/dashboard/uk/dev-2ii4bfcaymdes14b/applications/StFjKCcjSsjXKsAd7Dz85e5mI00LBceA/settings)

### Other authentication providers

It is possible to set up your own authentication provider. This can be done on any providers such as
auth0, okta, google, etc. To do this you will need to:
 You will have to configure the values in clusters/local_with_auth/values.yaml:oauth2-proxy.config.

To do this with auth0:
- create an account with auth0
- create an application
- create a user in the application
- set the callback URL to `https://oauth.phoenix.local/oauth2/callback`
- copy the client id and secret to the cluster/local_with_auth/secrets.yaml file
- update the `oidc_issuer_url` and `whitelist_domains` in cluster/local_with_auth/values.yaml to
  match the auth0 domain for the app.
- once the local cluster is up you should be redirected to the auth0 login page if you go to
  `https://api.phoenix.local/`
