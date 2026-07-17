---
name: azure-fastapi-easy-auth
description: Secure and troubleshoot FastAPI on Azure Functions or Azure App Service with Microsoft Entra App Service Authentication (Easy Auth). Use this skill whenever a request involves configuring authsettingsV2 Bicep, debugging a 401 or 403 before FastAPI, validating Entra audiences or caller applications, designing delegated vs app-only vs managed identity access, handling tenant consent or Conditional Access, or automating azd and Azure CLI authentication smoke tests. Trigger even when the user only says that a valid bearer token is rejected by an Azure-hosted FastAPI API.
compatibility: Requires Python 3.10+ for bundled diagnostics. Azure CLI, Azure Developer CLI, and Bicep are optional and needed only for Azure preflight, deployment, or template compilation.
---

# Azure FastAPI Easy Auth

Treat authentication as a chain of independently provable layers. A token from
Microsoft Entra ID proves issuance, not that Easy Auth accepted or authorized
the HTTP request.

Resolve `<skill-directory>` to the directory containing this `SKILL.md`. Use
that resolved path for bundled scripts, tests, examples, and Bicep assets so the
commands work from a user-wide symlink or any project directory.

## Safety boundary

- Never print, log, save, paste, or place bearer tokens on a command line.
- Use client IDs and tenant IDs only as nonsecret identifiers. Keep credentials
  in managed identity, workload federation, certificates, or secret stores.
- Do not bypass consent or Conditional Access. Record the policy decision and
  route it to the tenant owner.
- Do not use a delegated Azure CLI user token for unattended production
  automation. It is a bounded diagnostic or developer validation path.
- Label live evidence, local static evidence, documented guarantees, and
  empirical observations separately.

## Intake

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

## Choose the flow

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

## Model the four auth layers

1. **Token issuance:** The client obtained a token from the intended tenant.
2. **JWT validity:** Version, signature metadata, issuer, tenant, time,
   audience, permission, and caller claims match the resource contract.
3. **Easy Auth authentication and authorization:** The platform accepts the
   token and its caller application or principal before forwarding the request.
4. **FastAPI and business authorization:** FastAPI receives the request, then
   enforces scopes, roles, ownership, and data rules.

Never collapse these into "auth passed." Report evidence for each layer.

## Define durable registrations

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

## Write tests before configuration

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

## Compose `authsettingsV2`

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

## Preflight and deploy

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

## Validate safely

Read [references/diagnostics.md](references/diagnostics.md), then use
[scripts/easy_auth_probe.py](scripts/easy_auth_probe.py). The script keeps
tokens in memory, emits only claim booleans, and probes both `/.auth/me` and a
DB-free FastAPI endpoint.

Required matrix:

| Control | Expected | Meaning |
| --- | ---: | --- |
| No token | 401 | Authentication required |
| Wrong audience | 401 (empirical control) | Token rejected for this API |
| Valid token, unauthorized caller | 403 | Platform caller authorization denied |
| Valid token, authorized caller | 200 | Platform forwarded request |
| FastAPI probe marker | true | Request reached FastAPI |

The exact wrong-audience status is an empirical check. The documented contract
is that built-in authorization policy failures return 403, while the configured
unauthenticated action handles missing or invalid credentials.

## Diagnose from evidence

1. **No token is not denied:** Fix `globalValidation`, site selection, or path
   exclusions.
2. **Wrong audience is accepted:** Remove foreign audiences immediately.
3. **Expected token gets 401:** Check token version, issuer, tenant, audience,
   time, signature metadata, and deployed settings.
4. **Expected token gets 403:** Compare `azp` for v2 or `appid` for v1 with
   `allowedApplications`; then check allowed principals.
5. **`/.auth/me` and FastAPI return the same denial:** Treat it as platform
   denial before FastAPI.
6. **`/.auth/me` succeeds but FastAPI fails:** Inspect route, proxy, app code,
   scopes, roles, and business authorization.
7. **No endpoint exists or deployment failed:** Stop auth diagnosis and fix
   infrastructure or package deployment first.

Do not diagnose a generic 403 from status alone. Capture the safe claim summary,
deployed settings, both platform and app probes, and deployment evidence.

## Handle consent and Conditional Access

Read [references/governance.md](references/governance.md).

- Name the resource API, permission type, exact scope or role, and consuming
  client in every consent request.
- Keep custom API scopes distinct from Microsoft Graph permissions.
- Treat preauthorization, tenant consent, Easy Auth client policy, and FastAPI
  authorization as separate controls.
- If Conditional Access requires user interaction, stop unattended delegated
  automation. Use managed identity or app-only where the workload has no user.
- Do not weaken tenant policy to make a smoke test pass.

## Cleanup and stop conditions

- Use explicit ownership tags or manifests for transient Azure cleanup.
- Give retained diagnostic resources an owner and expiry time.
- Preserve durable resource apps, client apps, service principals, consent, and
  app-role assignments unless deletion was explicitly approved.
- Securely remove any temporary Azure CLI profile after an authorized fresh
  token experiment.
- Stop before mutation when ownership, tenant authority, or consent authority is
  unclear.

## Anti-patterns

| Anti-pattern | Exact remediation |
| --- | --- |
| "Azure CLI returned a token, so the API is healthy" | Run JWT, platform, FastAPI, and business proofs separately |
| Create, test, and delete an app registration per run | Use a governed durable registration and read-only per-run verification |
| Add broad audiences until 401 disappears | Derive audiences only from the same resource API token contract |
| Treat `preAuthorizedApplications` as an Easy Auth allowlist | Configure `allowedApplications` from `azp` or `appid` evidence |
| Pair a v1 issuer with `/v2.0` | Use the metadata endpoint matching the emitted token version |
| Use a delegated CLI token in production CI | Use managed identity, workload federation, certificate, or approved secret |
| Request a Graph permission for a custom API | Request the custom API scope or app role from that resource |
| Log the JWT to inspect it | Decode in memory and emit only redacted booleans |
| Diagnose auth before deployment succeeds | Prove provision and package deployment first |
| Delete all app registrations during cleanup | Delete only resources with explicit transient ownership |

## Report structure

Return this structure:

```markdown
# Easy Auth validation report
## Architecture decision
## Token issuance proof
## JWT contract proof
## Easy Auth authentication proof
## Easy Auth authorization proof
## FastAPI ingress proof
## Business or database proof
## Infrastructure and deployment proof
## Governance and consent status
## Cleanup and retained resources
## Limitations and evidence classification
```

For each proof, state `pass`, `fail`, `blocked`, or `not run`; identify evidence
as `live`, `local static`, `documented`, or `empirical`; and name the next
bounded action. Never report later layers as passed when an earlier layer is
blocked.

## References

- Registration and flow design:
  [references/architecture-and-flows.md](references/architecture-and-flows.md)
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
