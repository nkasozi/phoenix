# Prefect Server Ingress Setup with Authentication

This guide explains how to set up the Prefect server ingress with role-based authentication using
OAuth2. We'll use Auth0 as a concrete example, but the same principles apply to other OIDC
providers.

## Overview

The Prefect server ingress allows you to expose the Prefect UI externally with authentication
protection. It supports role-based access control through OIDC group claims, meaning only users with
specific roles can access the Prefect server.

**Key features:**
- Authentication via oauth2-proxy
- Role-based access control using OIDC groups/roles claims
- TLS support via cert-manager
- CORS configuration for cross-origin requests

## Prerequisites

Before setting up the Prefect server ingress, ensure you have:

1. **Prefect server enabled** in your values:
   ```yaml
   prefect-server:
     enabled: true
   ```

2. **oauth2-proxy configured** with your OIDC provider

3. **An OIDC provider** (Auth0, Okta, Google, etc.) with:
   - An application/client configured
   - Users with assigned roles
   - A custom claim for roles (required for group-based access)

## Configuration

### Enable the Prefect Server Ingress

Add the following to your cluster's `values.yaml`:

```yaml
prefectServerIngress:
  enabled: true
  # Comma-separated list of roles allowed to access the Prefect server
  allowedRoles: "admin"
```

The `allowedRoles` parameter accepts a comma-separated list of roles. Users must have at least one
of these roles to access the Prefect server.

### Configure oauth2-proxy for Role-Based Access

The oauth2-proxy must be configured to read roles from your OIDC provider's token. Add the
`oidc_groups_claim` setting to your oauth2-proxy configuration:

```yaml
oauth2-proxy:
  config:
    configFile: |
      provider="oidc"
      # ... other settings ...

      # The claim in the OIDC token that contains user roles
      oidc_groups_claim="https://your-domain.com/roles"
```

The value of `oidc_groups_claim` must match the claim name used by your OIDC provider.

## Auth0 Setup Example

This section provides a complete example of setting up Prefect server ingress with Auth0.

### Step 1: Create an Auth0 Application

1. Log in to your [Auth0 Dashboard](https://manage.auth0.com/)
2. Go to **Applications** > **Create Application**
3. Select **Regular Web Application**
4. Configure the application settings:
   - **Allowed Callback URLs**: `https://oauth.<your-domain>/oauth2/callback`
   - **Allowed Logout URLs**: `https://oauth.<your-domain>/oauth2/sign_out`
   - **Allowed Web Origins**: `https://console.<your-domain>`

### Step 2: Create Roles in Auth0

1. Go to **User Management** > **Roles**
2. Create a role named `admin` (or whatever roles you want to use)
3. Assign the role to users who should have Prefect access

### Step 3: Create an Auth0 Action to Add Roles to Tokens

Auth0 doesn't include roles in tokens by default. You need to create an Action to add them.

1. Go to **Actions** > **Library** > **Build Custom**
2. Create a new Action with the following code:

```javascript
exports.onExecutePostLogin = async (event, api) => {
  const namespace = 'https://your-domain.com';

  const roles = event.authorization?.roles || [];
  // Add roles to the ID token
  api.idToken.setCustomClaim(`${namespace}/roles`, roles);
  // Add roles to the access token (optional)
  api.accessToken.setCustomClaim(`${namespace}/roles`, roles);
};
```

3. Deploy the Action
4. Go to **Actions** > **Triggers** > **post-login**
5. Add your new Action to the Login flow

**Important:** The namespace (e.g., `https://your-domain.com`) must be a URL format and should match
what you configure in `oidc_groups_claim`.

### Step 4: Configure Phoenix Values

Create or update your cluster's `values.yaml`:

```yaml
base_host: "your-domain.com"
base_schema: "https"

use_local_insecure_auth: false

oauth2-proxy:
  config:
    configFile: |
      provider="oidc"
      provider_display_name="Auth0"
      oidc_issuer_url="https://<your-auth0-tenant>.auth0.com/"
      code_challenge_method="S256"
      http_address="0.0.0.0:4180"
      upstreams="file:///dev/null"
      email_domains="*"

      # Cookie configuration
      cookie_httponly=false
      cookie_domains=".<your-domain.com>"
      cookie_samesite="lax"
      cookie_secure="true"

      # Whitelist your domain and Auth0 domain
      whitelist_domains=["*.<your-domain.com>:*", "<your-auth0-tenant>.auth0.com"]

      # Required scopes
      scope="openid email"

      # Pass authentication headers to backend services
      pass_access_token=true
      pass_authorization_header=true
      pass_user_headers=true
      set_xauthrequest=true

      # IMPORTANT: This must match the claim namespace in your Auth0 Action
      oidc_groups_claim="https://your-domain.com/roles"

# Enable Prefect server
prefect-server:
  enabled: true

# Enable Prefect server ingress with role restriction
prefectServerIngress:
  enabled: true
  allowedRoles: "admin"
```

### Step 5: Configure Secrets

Create a `secrets.yaml` file with your Auth0 credentials:

```yaml
oauth2-proxy:
  config:
    cookieSecret: "<generate-a-random-32-byte-base64-string>"
    clientID: "<your-auth0-client-id>"
    clientSecret: "<your-auth0-client-secret>"
```

You can generate a cookie secret with:
```bash
python -c 'import os,base64; print(base64.b64encode(os.urandom(32)).decode())'
```

## Accessing the Prefect Server

Once deployed, the Prefect server will be available at:
```
https://prefect.<your-domain>/
```

Users will be redirected to Auth0 for authentication. Only users with the roles specified in
`allowedRoles` will be granted access.

## How It Works

The Prefect server ingress uses nginx-ingress annotations to enforce authentication:

1. **Auth URL**: Requests are authenticated against oauth2-proxy with the `allowed_groups` parameter
2. **Auth Response Headers**: User information is passed to the backend via headers:
   - `x-auth-request-user`: Username
   - `x-auth-request-groups`: User's groups/roles
   - `x-auth-request-email`: User's email

The ingress template (`charts/main/templates/prefect-server-ingress.yaml`) configures:
```yaml
nginx.ingress.kubernetes.io/auth-url: http://<release>-oauth2-proxy.<namespace>.svc.cluster.local/oauth2/auth?allowed_groups=<allowedRoles>
```

## Troubleshooting

### Users cannot access despite having the correct role

1. **Check the Auth0 Action is deployed and in the Login flow**
2. **Verify the roles claim is in the token**: Use [jwt.io](https://jwt.io) to decode your token
   and check for the roles claim
3. **Ensure `oidc_groups_claim` matches your Auth0 Action namespace exactly**
4. **Check oauth2-proxy logs** for authentication errors:
   ```bash
   kubectl logs -l app.kubernetes.io/name=oauth2-proxy
   ```

### 403 Forbidden errors

This typically means authentication succeeded but authorization failed:
- Verify the user has the required role in Auth0
- Check that the role name in Auth0 matches `allowedRoles` exactly (case-sensitive)

### Redirect loops or cookie issues

- Ensure `cookie_domains` includes your base domain with a leading dot
- Verify `whitelist_domains` includes both your domain and the Auth0 domain
- Check that `cookie_secure` matches your schema (true for https)

## Other OIDC Providers

### Okta

For Okta, use the groups claim from your Okta authorization server:

```yaml
oauth2-proxy:
  config:
    configFile: |
      provider="oidc"
      oidc_issuer_url="https://<your-okta-domain>/oauth2/default"
      oidc_groups_claim="groups"
      # ... other settings
```

### Google

Google Workspace can use group memberships. Configure oauth2-proxy to use Google-specific settings:

```yaml
oauth2-proxy:
  config:
    configFile: |
      provider="google"
      google_admin_email="admin@your-domain.com"
      google_service_account_json="/path/to/service-account.json"
      # Groups are read automatically from Google Workspace
```

## Related Documentation

- [oauth2-proxy documentation](https://oauth2-proxy.github.io/oauth2-proxy/)
- [Auth0 Actions documentation](https://auth0.com/docs/customize/actions)
- [Prefect Server documentation](https://docs.prefect.io/latest/guides/host/)
- [charts/main/README.md](../charts/main/README.md) - Main chart documentation
