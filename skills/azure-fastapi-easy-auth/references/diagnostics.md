# Safe diagnostics

## Diagnostic script

The script at
[`scripts/easy_auth_probe.py`](../scripts/easy_auth_probe.py):

- acquires a delegated token from the existing Azure CLI session or reads a
  token from standard input;
- never prints or writes the token;
- decodes claims in memory without claiming cryptographic validation;
- emits booleans for issuer, tenant, audience, permission, and caller;
- sends no-token, optional wrong-audience, and expected-token probes;
- reads only a bounded response body;
- marks whether the FastAPI probe returned `layer: fastapi`.

Approved delegated public client:

```bash
uv run --with msal python \
  "<skill-directory>/scripts/easy_auth_probe.py" \
  --endpoint "https://<site-host>" \
  --tenant-id "$ENTRA_TENANT_ID" \
  --resource-app-id "$ENTRA_RESOURCE_APP_ID" \
  --allowed-client-id "$CALLER_CLIENT_ID" \
  --expected-scope access_as_user \
  --device-code-client-id "$CALLER_CLIENT_ID" \
  --device-code-timeout 600 \
  --include-wrong-audience-control
```

This device-code flow presents the actual approved caller in the token's
`azp`. Use `--azure-cli-scope` only when Azure CLI itself is intentionally
preauthorized and present in Easy Auth `allowedApplications`; it cannot mint a
token whose `azp` impersonates another client registration.

App-only or managed identity token from a secure producer:

```bash
secure-token-producer |
  python3 "<skill-directory>/scripts/easy_auth_probe.py" \
    --endpoint "https://<site-host>" \
    --tenant-id "$ENTRA_TENANT_ID" \
    --resource-app-id "$ENTRA_RESOURCE_APP_ID" \
    --allowed-client-id "$CALLER_CLIENT_ID" \
    --expected-role Api.Invoke \
    --token-stdin
```

Do not place the token in an argument, environment variable, file, or shell
history. Ensure the producer also avoids logging.

## Claim interpretation

| Signal | Delegated v2 | Delegated v1 | App-only |
| --- | --- | --- | --- |
| Permission | `scp` | `scp` | `roles` |
| Caller client | `azp` | `appid` | `azp` or `appid` by version |
| Client auth method | `azpacr` | `appidacr` | same version rule |
| User context | present | present | absent |

The script only inspects claims. Easy Auth or a JWT library must perform
signature and lifetime validation.

## Evidence-driven decision tree

### Token cannot be acquired

Inspect tenant selection, resource scope, consent, Conditional Access, and user
interaction requirements. Do not edit Easy Auth because the request has not
reached it.

### Token summary mismatches

- Wrong `aud`: request the token for the resource API, do not widen audiences.
- Wrong `iss` or `tid`: acquire from the intended tenant and align issuer.
- Missing `scp`: request and consent the custom delegated scope.
- Missing `roles`: assign and consent the resource API application role.
- Wrong `azp` or `appid`: identify the actual client and update policy only if
  it is an approved caller.

### 401 at `/.auth/me` and FastAPI

Compare deployed `openIdIssuer`, allowed audiences, token version, tenant, and
site selection. Check token expiration and service time. Keep token store
behavior in mind: Microsoft documents `/.auth/me` token retrieval when token
store is enabled.

### 403 at `/.auth/me` and FastAPI

Check `defaultAuthorizationPolicy`. `allowedApplications` evaluates `azp` for
v2 and `appid` for v1. Check allowed principals if configured. This is distinct
from resource-app preauthorization.

### Platform endpoint succeeds, FastAPI fails

Inspect route and proxy settings, then application checks for scopes, roles,
tenant, principal, and ownership. Use a DB-free route before testing storage or
database access.

## Azure CLI cache

An existing Azure CLI cache can make repeated acquisition appear healthier than
a new interactive session. First report that the token came from the existing
CLI context. If a fresh issuance experiment is necessary:

1. obtain explicit approval for interactive sign-in;
2. create a private temporary `AZURE_CONFIG_DIR`;
3. sign in to the exact tenant;
4. run one bounded probe;
5. sign out, unset the variable, and securely remove the directory;
6. report only booleans and timings.

Example local isolation:

```bash
TEMP_AZURE_CONFIG="$(mktemp -d)"
chmod 700 "$TEMP_AZURE_CONFIG"
export AZURE_CONFIG_DIR="$TEMP_AZURE_CONFIG"
az login --tenant "$ENTRA_TENANT_ID"

# Run the bounded probe here.

az logout
unset AZURE_CONFIG_DIR
rm -rf "$TEMP_AZURE_CONFIG"
```

This is a diagnostic technique, not production automation. Do not use it to
evade Conditional Access.

## Logging

Enable App Service application logging and, where available, failed request
tracing. Look for the Easy Auth module in failed-request evidence. AppLens and
plan-specific logs can be incomplete, so retain the HTTP controls and deployed
settings even when platform logs are sparse.

Retained diagnostics need:

- owner;
- reason;
- creation time;
- expiry time;
- exact changed settings;
- rollback procedure;
- confirmation that no token was stored.
