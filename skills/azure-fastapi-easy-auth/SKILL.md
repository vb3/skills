---
name: azure-fastapi-easy-auth
description: Scaffold, secure, deploy, and troubleshoot FastAPI on Azure Functions or Azure App Service with Microsoft Entra App Service Authentication (Easy Auth). Use this skill for a fresh FastAPI Functions setup, authsettingsV2 Bicep, azd deployment, 401 or 403 before FastAPI, Entra audiences or caller applications, delegated vs app-only vs managed identity access, consent, Conditional Access, or auth smoke tests. Default to the fresh setup fast path and load debugging guidance only after a setup gate fails.
compatibility: Requires Python 3.10+. The complete fresh setup uses Azure CLI, Azure Developer CLI, Bicep, Azure Functions Core Tools, and uv with the MSAL Python package for the approved-caller device-code probe.
---

# Azure FastAPI Easy Auth

Treat authentication as a chain of independently provable layers. A token from
Microsoft Entra ID proves issuance, not that Easy Auth accepted or authorized
the HTTP request.

Resolve `<skill-directory>` to the directory containing this `SKILL.md`. Use
that resolved path for bundled scripts, tests, examples, and Bicep assets so the
commands work from a user-wide symlink or any project directory.

## Fresh setup fast path

Use this path by default for a new or minimal repository. Read
[references/fresh-setup.md](references/fresh-setup.md) and execute its seven
gates in order:

1. Scaffold FastAPI, `AsgiFunctionApp`, `azure.yaml`, and Flex Bicep with
   [scripts/scaffold_fastapi_flex.py](scripts/scaffold_fastapi_flex.py).
2. Prove the DB-free `/auth/probe` locally through Functions Core Tools.
3. Create once or verify the durable v2 resource API with
   [scripts/bootstrap_resource_app.py](scripts/bootstrap_resource_app.py).
4. Set the tenant, resource app, approved caller, and Flex region in azd.
5. Run tests, compile Bicep, and run the read-only Azure preflight.
6. Run `azd provision`, then `azd deploy`.
7. Run the no-token, wrong-audience, and approved-token matrix to prove the
   first FastAPI 200.

This ordering prevents the known setup time sinks before they occur:

- durable directory objects avoid create-token-delete propagation races;
- the v2 GUID audience is configured before deployment;
- `preAuthorizedApplications` and Easy Auth `allowedApplications` receive the
  same approved caller but remain separate controls;
- tenant consent is evaluated from current evidence rather than assumed;
- provider, region, deployment, and host-startup failures are resolved before
  HTTP auth diagnosis.

If all seven gates pass, stop. Do not load debugging references during a clean setup.

## Detailed workflow

Use the remaining sections when the project is not greenfield, has multiple
caller types, or needs architecture and governance decisions beyond the first
authenticated response.

### Safety boundary

- Never print, log, save, paste, or place bearer tokens on a command line.
- Use client IDs and tenant IDs only as nonsecret identifiers. Keep credentials
  in managed identity, workload federation, certificates, or secret stores.
- Do not bypass consent or Conditional Access. Record the policy decision and
  route it to the tenant owner.
- Do not use a delegated Azure CLI user token for unattended production
  automation. It is a bounded diagnostic or developer validation path.
- Label live evidence, local static evidence, documented guarantees, and
  empirical observations separately.

### Intake

Collect these facts before changing an app registration or infrastructure:

| Concern | Required facts |
| --- | --- |
| Hosting | Azure Functions plan or App Service plan, OS, region, runtime |
| Ingress | Public endpoint, private endpoint, VNet integration, proxy or gateway |
| Tenant | Workforce tenant, single or multitenant registration, governance owner |
| Callers | Browser, SPA/native client, external daemon, Azure-hosted workload |
| Flow | Delegated user, app-only client credentials, managed identity |
| Token | `ver`, expected `aud`, `iss`, `tid`, `scp` or `roles`, `azp` or `appid` |
| Resource API | Client ID, Application ID URI, scopes, app roles, token version |
| Delivery | Bicep/ARM, azd, Azure CLI, deployment package mechanism |
| Authorization | Allowed caller apps, principals, scopes, roles, business checks |
| Ownership | Durable directory objects, transient resources, cleanup markers |

Stop and ask if the resource API, intended caller, tenant, or authorization
semantics are unknown. Guessing at an audience or widening a client allowlist
can authorize a token intended for the wrong API or caller.

### Choose the flow

Read [references/architecture-and-flows.md](references/architecture-and-flows.md)
for the complete registration model.

| Need | Flow | Token authorization |
| --- | --- | --- |
| Act with a signed-in user | Delegated authorization code flow | `scp`, plus user/business policy |
| Azure-hosted service-to-service | Managed identity | Resource app role and caller identity |
| External daemon or CI | App-only client credentials | Application `roles`; prefer federation or certificate |
| Same-origin browser site | Easy Auth browser session | Cookie at platform, application authorization in API |

Use managed identity for an Azure-hosted worker when the target accepts Entra
tokens. Use app-only for a workload with no user. Use delegated access only
when the operation genuinely needs user context.

### Model the four auth layers

1. **Token issuance:** The client obtained a token from the intended tenant.
2. **JWT validity:** Version, signature metadata, issuer, tenant, time,
   audience, permission, and caller claims match the resource contract.
3. **Easy Auth authentication and authorization:** The platform accepts the
   token and its caller application or principal before forwarding the request.
4. **FastAPI and business authorization:** FastAPI receives the request, then
   enforces scopes, roles, ownership, and data rules.

Never collapse these into "auth passed." Report evidence for each layer.

### Define durable registrations

Separate lifecycle responsibilities:

1. Create and govern the resource API app registration once.
2. Expose only the delegated scopes and application roles the API implements.
3. Register each independent client. Preauthorize a delegated client only when
   tenant governance permits it.
4. Record the tenant consent decision. Grant consent or assign an app role only
   when the permission type and tenant policy require it.
5. During each deployment, verify registrations and grants read-only.
6. Clean transient Azure resources separately. Do not delete durable
   registrations or grants unless an explicit ownership marker authorizes it.

`api.preAuthorizedApplications` controls delegated consent prompts for scopes.
It does not configure Easy Auth caller authorization and does not override
tenant consent or Conditional Access.

### Write tests before configuration

Create static contract tests before editing Bicep or scripts:

- expected issuer matches the token version and tenant;
- v2 GUID audience is present;
- any optional Application ID URI belongs to the same resource API;
- the expected caller IDs are in `allowedApplications` when client allowlisting
  is part of the design;
- token store and unauthenticated action have intentional values;
- no secret value is embedded;
- negative and positive HTTP cases are declared.

Use the synthetic fixtures and tests in this skill:

```bash
python3 -m unittest discover \
  -s "<skill-directory>/tests" -v
```

### Compose `authsettingsV2`

Read
[references/easy-auth-configuration.md](references/easy-auth-configuration.md),
then start from
[assets/bicep/easy-auth.bicep](assets/bicep/easy-auth.bicep).
Resolve its executable path as
`<skill-directory>/assets/bicep/easy-auth.bicep`.

1. Enable the platform and require HTTPS.
2. For APIs, require authentication and return 401 for missing or invalid
   credentials.
3. Use a tenant and token-version-correct `openIdIssuer`.
4. Derive allowed audiences from the actual resource token contract.
5. Add only caller client IDs to
   `defaultAuthorizationPolicy.allowedApplications`.
6. Keep token store disabled unless `/.auth/me`, refresh behavior, or downstream
   provider tokens are required.
7. Select `NoProxy`, `Standard`, or `Custom` forwarding behavior from the real
   Front Door, Application Gateway, or direct-ingress topology.
8. Preserve application-level scope, role, and business authorization.

For v2 access tokens, `aud` is the resource API client GUID. An `api://` URI can
be included for a v1 or custom resource form only after proving it identifies
the same resource API. Never add Microsoft Graph or Azure management audiences
to make an API token pass.

### Preflight and deploy

Read
[references/deployment-and-networking.md](references/deployment-and-networking.md).

1. Run local tests and compile Bicep.
2. Run the read-only provider and region preflight.
3. Verify durable directory objects and consent separately.
4. Provision infrastructure with `azd provision` or `azd up`.
5. Confirm provisioning and package deployment succeeded before HTTP auth
   diagnosis.
6. Read back `authsettingsV2`.
7. Run the controlled HTTP matrix.
8. Run database or business proof only after FastAPI proof.

For Functions Flex with VNet integration, check regional availability and the
`Microsoft.App` provider before provisioning. A provision, package, or
OneDeploy failure is not an Easy Auth failure.

### Handle consent and Conditional Access

Read [references/governance.md](references/governance.md).

- Name the resource API, permission type, exact scope or role, and consuming
  client in every consent request.
- Keep custom API scopes distinct from Microsoft Graph permissions.
- Treat preauthorization, tenant consent, Easy Auth client policy, and FastAPI
  authorization as separate controls.
- If Conditional Access requires user interaction, stop unattended delegated
  automation. Use managed identity or app-only where the workload has no user.
- Do not weaken tenant policy to make a smoke test pass.

### Identity and diagnostic cleanup boundaries

- Delete only transient Azure resources with explicit ownership markers.
- Preserve resource apps, client apps, service principals, consent, and
  app-role assignments unless their owner explicitly approves deletion.
- Give retained diagnostics an owner and expiry, and remove any temporary Azure
  CLI profile after an authorized fresh-token experiment.
- Do not mutate directory objects when ownership or tenant authority is unclear.

## Debug path

Enter this path only after a fresh-setup gate fails or when the user explicitly
asks to troubleshoot an existing deployment.

- Token issuance, consent, or Conditional Access failure: load
  [references/governance.md](references/governance.md).
- Provider, region, provision, package, startup, or network failure: load
  [references/deployment-and-networking.md](references/deployment-and-networking.md).
- HTTP 401 or 403: load
  [references/diagnostics.md](references/diagnostics.md) and use
  [scripts/easy_auth_probe.py](scripts/easy_auth_probe.py).
- Load [references/friction-analysis.md](references/friction-analysis.md) only
  when the immediate evidence does not isolate the failure.

Do not load every debugging reference speculatively. Stop at the first failed
layer, report its evidence as `live`, `local static`, `documented`, or
`empirical`, and leave later layers as `not run`.

## Setup result

For a clean setup, report only:

```markdown
## Scaffold
## Resource API
## Provision and deployment
## Easy Auth controls
## First FastAPI 200
## Remaining production decisions
```

Use the longer layered report in `references/diagnostics.md` only for a failed
or audited deployment.

## References

- Registration and flow design:
  [references/architecture-and-flows.md](references/architecture-and-flows.md)
- Fresh Functions Flex setup:
  [references/fresh-setup.md](references/fresh-setup.md)
- Easy Auth and Bicep:
  [references/easy-auth-configuration.md](references/easy-auth-configuration.md)
- Hosting and deployment:
  [references/deployment-and-networking.md](references/deployment-and-networking.md)
- Safe diagnostics:
  [references/diagnostics.md](references/diagnostics.md)
- Consent and Conditional Access:
  [references/governance.md](references/governance.md)
- Generalized observed friction:
  [references/friction-analysis.md](references/friction-analysis.md)
- Primary Microsoft sources:
  [references/sources.md](references/sources.md)
