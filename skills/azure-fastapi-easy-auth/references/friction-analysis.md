# Friction analysis

This analysis generalizes anonymized implementation evidence. Rows marked
empirical describe observed platform behavior and must be revalidated in the
target environment.

| Symptom | Wrong assumption | Evidence that isolated it | Generalized guardrail |
| --- | --- | --- | --- |
| Token command succeeds, endpoint fails | Token issuance proves API access | Claims matched, but both platform and app probes denied | Prove issuance, JWT contract, platform, and app separately |
| New app works inconsistently | Create and delete is clean isolation | Stable objects removed propagation from the critical path | Separate durable directory lifecycle from transient Azure lifecycle |
| User is prompted for consent | Preauthorization overrides tenant policy | Manifest and tenant policy remained independent | Treat preauthorization as consent UX, not policy bypass |
| Earlier transient flow reports admin approval | Admin consent must precede every retry | A durable app issued a token without a tenant-wide delegated grant | Escalate consent only when current policy or issuance evidence requires it |
| v2 token receives 401 | `api://` is always the v2 audience | Safe claim summary showed a GUID `aud` | Configure the actual v2 GUID; add URI only for the same API when needed |
| Issuer validation fails | Any tenant URL with `/v2.0` is valid | Token `ver` and `iss` disagreed with deployed issuer | Match the metadata endpoint and issuer to token version |
| Valid token receives platform 403 | Scope and audience are sufficient | Both `/.auth/me` and FastAPI changed from 403 to 200 after one caller allowlist change | Compare `azp` or `appid` with `allowedApplications` |
| Generic 403 has no useful logs | Logs will name the failed claim | HTTP controls and safe claims were more complete than plan logs | Preserve matrix, deployed settings, and booleans even when logs are sparse |
| Repeated CLI acquisition succeeds | Every token was freshly issued | Existing profile and broker state could not prove freshness | Label cache context; isolate a temporary profile only with approval |
| Delegated automation stalls | User tokens are suitable for CI | Conditional Access required interaction | Use managed identity or app-only for userless automation |
| Consent request asks for Graph | Similar scope wording means same permission | The token audience belonged to the custom resource API | Name exact resource, scope or role, and client |
| Auth testing never starts | Capacity error is an auth blocker | Provision stopped before an endpoint existed | Classify region, provider, quota, provision, deployment, and auth separately |
| Cleanup risks durable identity | Everything created for testing is disposable | Registration ownership and cloud environment ownership differed | Delete only explicit transient ownership; give retained diagnostics a TTL |

## Empirical 403 to 200 observation

See the full
[anonymized restrictive-tenant case study](governance.md#anonymized-restrictive-tenant-case-study).
The reusable facts are that token issuance succeeded without a tenant-wide
delegated grant, platform authorization still returned 403, and allowing the
approved caller client changed only expected-token probes to 200. Consent
escalation therefore remains conditional, while Easy Auth caller authorization
remains a separate required check.

Microsoft documents that built-in authorization policy uses `appid` or `azp`
and returns 403 on failure. The exact status matrix for malformed, expired, and
wrong-audience tokens remains an environment-specific empirical check.

## Propagation observation

A create-token-delete loop made application, service-principal, scope, consent,
and token-service convergence part of each run. Reusing a stable resource app
removed that churn. This supports the durable lifecycle guardrail, but it does
not prove replication was the only cause of every earlier token failure.

## Infrastructure observation

Region capability, model quota, SQL capability, provider registration, private
networking, and package deployment can fail before an HTTP endpoint exists.
Report those as infrastructure or deployment blockers. Do not infer an Easy
Auth result from a token-only or static Bicep proof.
