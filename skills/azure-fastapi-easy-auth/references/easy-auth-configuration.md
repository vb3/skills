# Easy Auth configuration

## Bicep module

The module at
[`assets/bicep/easy-auth.bicep`](../assets/bicep/easy-auth.bicep) targets an
existing `Microsoft.Web/sites` resource, so it applies to Azure Functions and
Azure App Service.

It defaults to:

- platform authentication enabled;
- authentication runtime `~1`, the documented value for the latest supported
  middleware version;
- HTTPS required;
- authentication required;
- API-style 401 for unauthenticated requests;
- v2 tenant issuer;
- resource client GUID plus optional `api://` URI for the same resource;
- an explicit caller client allowlist when the supplied array is nonempty;
- token store disabled.

Compile it without Azure mutation:

```bash
az bicep build \
  --file "<skill-directory>/assets/bicep/easy-auth.bicep" \
  --stdout >/dev/null
```

Example invocation:

```bicep
module easyAuth 'easy-auth.bicep' = {
  name: 'easy-auth'
  params: {
    siteName: site.name
    tenantId: entraTenantId
    resourceAppClientId: resourceAppClientId
    allowedClientApplicationIds: allowedClientApplicationIds
    includeApplicationIdUriAudience: true
    tokenStoreEnabled: false
    forwardProxyConvention: 'NoProxy'
  }
}
```

Use `Standard` for supported standard proxy forwarding. Use `Custom` with
`forwardProxyCustomHostHeaderName` and
`forwardProxyCustomProtoHeaderName` when the ingress supplies custom original
host and protocol headers. Verify those header names against the gateway
configuration rather than guessing.

## Issuer

Use the issuer metadata endpoint matching the access token version:

| Token | Expected issuer form |
| --- | --- |
| v2 | `https://login.microsoftonline.com/<tenant-id>/v2.0` |
| v1 | `https://sts.windows.net/<tenant-id>/` |

Do not append `/v2.0` to `sts.windows.net`. For sovereign clouds, derive the
login endpoint from the Azure environment rather than hardcoding the global
endpoint.

## Audiences

For a v2 access token, `aud` is the resource API client GUID. For a v1 token it
can be a client GUID or resource URI. Start with the GUID. Include an
Application ID URI only when token evidence and the resource app manifest prove
that it identifies the same API.

Never add:

- Microsoft Graph as an allowed audience for a custom API;
- Azure Resource Manager as an allowed audience for a custom API;
- an unrelated client's ID;
- a wildcard or a URI copied from another environment.

An access token for another API does not become valid because it has a useful
scope name.

## Caller authorization

`defaultAuthorizationPolicy.allowedApplications` compares:

- v2 `azp`, or
- v1 `appid`.

It contains client application IDs, not resource app object IDs, service
principal object IDs, scope IDs, or user IDs. If both allowed applications and
allowed principals are configured, the built-in policy combines them with
logical AND.

`api.preAuthorizedApplications` belongs to the resource app manifest and
controls delegated consent prompts. It does not populate or replace
`allowedApplications`.

Built-in authorization policy failures return 403. Configure this policy through
ARM, Bicep, or REST because the portal does not expose every property.

The bundled module omits `defaultAuthorizationPolicy` when
`allowedClientApplicationIds` is empty. Make that an explicit architecture
decision. Passing an empty array avoids an accidental deny-all policy, but it
also removes platform caller-client restriction, so FastAPI scope or role
authorization remains essential.

## Token store

Keep token store disabled for a bearer-token API unless the application needs:

- `/.auth/me`;
- provider access or refresh tokens;
- Easy Auth refresh behavior.

Enabling token store expands retained token state. It does not authorize a
caller and should not be used as a 401 or 403 fix.

## Multitenant caution

Easy Auth does not automatically establish every tenant restriction needed by a
multitenant application. Validate the tenant and issuer in the application, or
use the documented tenant controls when they match the design. Never infer
tenant trust from audience alone.

## Read back deployed settings

Use a GET or list operation before diagnosis:

```bash
az rest --method GET \
  --url "$SITE_RESOURCE_ID/config/authsettingsV2/list?api-version=2024-04-01" \
  --query 'properties' \
  --output json
```

Do not paste the result into a public issue without checking app-setting names,
redirect URLs, tenant IDs, and client IDs. They are identifiers rather than
credentials, but they can still disclose environment topology.
