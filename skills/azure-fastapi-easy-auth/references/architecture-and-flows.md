# Architecture and authentication flows

## Layered trust model

| Layer | Owner | Evidence | Typical failure |
| --- | --- | --- | --- |
| Token issuance | Microsoft Entra ID and tenant policy | Token acquired for intended resource and tenant | Consent or Conditional Access error |
| JWT contract | Resource API | `ver`, `iss`, `tid`, `aud`, time, permission, caller | 401 or local mismatch |
| Easy Auth authentication | App Service platform | Missing/wrong token control and platform endpoint | 401 |
| Easy Auth authorization | App Service platform | Caller application or principal policy | 403 |
| FastAPI authorization | Application | Scope, role, ownership, and route checks | Application 403 |
| Business/data | Application and dependencies | DB-free probe, then dependency proof | App-specific error |

The API is the token audience and must validate the access token. A client must
not validate an access token and then forward it as if it were the API.

## Flow decision matrix

| Caller | Flow | Resource API permission | Preferred credential |
| --- | --- | --- | --- |
| Browser or native app acting for a user | Delegated authorization code | OAuth delegated scope in `scp` | User interaction, PKCE where the client supports it |
| Same-origin server-rendered browser app | Easy Auth sign-in session | Delegated scope or application policy | Easy Auth confidential-client setup |
| Azure Function, Web App, VM, or container | Managed identity | Application app role in `roles` | Managed identity token |
| External daemon or CI | Client credentials | Application app role in `roles` | Workload federation, certificate, then secret as last choice |
| Developer smoke test | Delegated CLI token | Custom delegated scope | Existing interactive CLI session, bounded to diagnostics |

Do not use delegated flow when there is no user. Do not use app-only flow when
the authorization decision must reflect the signed-in user.

## Registration relationships

### Resource API

Keep one durable resource app registration with:

- one Application ID URI, normally `api://<resource-client-id>`;
- `requestedAccessTokenVersion: 2` for a v2 contract;
- delegated scopes for user-context operations;
- app roles with `allowedMemberTypes: ["Application"]` for service callers;
- no Microsoft Graph permission unless the API itself calls Graph;
- no password or certificate credentials unless the resource app is also a
  confidential client for an explicit downstream flow.

### Delegated client

Register each SPA, native app, server web app, or diagnostic public client
separately. Grant the resource API's custom scope. A preauthorized client avoids
an additional user consent prompt for listed scopes, but tenant policy may still
require admin approval.

### App-only client

Register the workload and obtain authorized directory approval for the resource
API app-role assignment. The token should carry the role in `roles`. Also
restrict the caller in Easy Auth with `allowedApplications` when that policy
matches the design.

### Managed identity

The managed identity's service principal is the client identity. Assign it the
resource API app role. The acquired token still identifies a caller application
and must satisfy the API's Easy Auth and application authorization.

Managed identity can also replace the Easy Auth provider's stored client secret
through a user-assigned identity and federated identity credential. That is a
separate use from an Azure-hosted workload calling the API.

## Durable lifecycle

Split the lifecycle into two tracks:

| One-time governed track | Per-deployment track |
| --- | --- |
| Create resource and client registrations | Read registrations and service principals |
| Assign owners | Verify exact scopes, roles, URIs, and token version |
| Establish scopes and app roles | Verify consent and assignments |
| Record and, only when required, approve consent | Compile and deploy infrastructure |
| Record deletion authority | Run bounded token and HTTP controls |

Creating and deleting directory objects during every smoke test places directory
replication and token-service convergence on the critical path. Reuse durable,
owned objects and keep transient Azure resource cleanup independent.

## Application authorization

`allowedApplications` proves the token came through an expected client. It does
not prove the client has the right delegated scope or application role for an
operation. FastAPI must enforce:

- the expected `scp` value for delegated requests;
- the expected `roles` value for app-only requests;
- tenant and principal constraints not enforced by the platform configuration;
- resource ownership and business permissions.

When consuming Easy Auth headers, remember that the platform maps some claim
names in `X-MS-CLIENT-PRINCIPAL`. Test the header contract explicitly and do not
accept a directly supplied header on an endpoint that can bypass Easy Auth.
