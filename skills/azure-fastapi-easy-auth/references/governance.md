# Consent and Conditional Access

## Decision framework

Answer in order:

1. Is the operation on behalf of a user or a workload?
2. Is the permission a custom API scope, custom API app role, or Microsoft Graph
   permission?
3. Is user consent allowed for that permission and tenant?
4. Does tenant policy require admin consent or application assignment?
5. Does Conditional Access require MFA, device state, location, or recurring
   interaction?
6. Can a userless workload use managed identity or workload federation?
7. Who owns the resource app, client app, enterprise applications, consent, and
   future deletion?

Do not request broad Graph permissions when the target is a custom API. A
custom `access_as_user` scope is unrelated to Graph permissions with similar
words.

## Control boundaries

| Control | Purpose |
| --- | --- |
| Resource app scope or role | Defines what the API exposes |
| Client requested permission | Declares what the client needs |
| Preauthorized application | Suppresses listed delegated user-consent prompts |
| Tenant consent | Authorizes the permission under tenant governance |
| Conditional Access | Controls token issuance and session conditions |
| Easy Auth allowed applications | Restricts client applications at ingress |
| FastAPI authorization | Enforces operation and resource rules |

No single row replaces the others.

## Consent request content

State:

- resource API display name and client ID;
- consuming client display name and client ID;
- delegated scope or application role value;
- delegated or application permission type;
- users or workload covered;
- why least privilege is sufficient;
- owner and review date;
- revocation and cleanup plan.

Tenant-wide admin consent affects the organization. Requiring user assignment
is a separate control.

## Conditional Access response

If a delegated public-client flow requires recurring interaction:

- keep it interactive for developer validation;
- do not store a user's refresh token for automation;
- do not weaken policy or choose a legacy flow;
- redesign a userless job to managed identity or app-only;
- record when user context prevents that redesign.

## Anonymized restrictive-tenant case study

### Situation

A team needed a disposable FastAPI validation environment in a restrictive
enterprise tenant. A public developer client requested one custom delegated
scope. Recreating the resource app for every run caused propagation uncertainty,
and Conditional Access made unattended user-token acquisition unreliable.

### Wrong assumptions

- A token acquisition command proving success would prove HTTP access.
- Resource-app preauthorization would also authorize the caller in Easy Auth.
- Recreating the app registration would make cleanup simpler.

### Evidence

- A stable resource app eventually produced a token with the expected tenant,
  v2 GUID audience, scope, and caller claim.
- Read-only verification found no tenant-wide delegated `AllPrincipals` grant.
  Token issuance still succeeded, so an earlier admin-approval failure was not
  reproduced and did not prove that tenant-wide consent was required.
- Both the platform endpoint and FastAPI returned 403.
- Adding only the approved caller client ID to the Easy Auth application
  allowlist changed the expected-token probes to 200 while no-token and
  wrong-audience controls remained denied.

### Generalized decision

- Keep governed registrations and consent durable.
- Evaluate consent from current tenant policy and token-issuance evidence.
  Escalate only when the tenant actually requires it.
- Use delegated CLI access only for bounded interactive validation.
- Use managed identity for Azure-hosted service-to-service work.
- Use app-only federation or certificate credentials for external automation.
- Treat preauthorization, tenant governance, and Easy Auth authorization as
  distinct controls.

The likely difference between the earlier transient failure and the durable
success was lifecycle or propagation, but the retained evidence cannot prove a
single cause. The later 403 was a separate Easy Auth client-authorization
failure, not a token-issuance or tenant-consent failure.

This case is empirical evidence from one restricted environment, not a guarantee
that every tenant or hosting plan returns identical statuses or logs.
