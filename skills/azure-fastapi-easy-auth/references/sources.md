# Official Microsoft sources

Verified on 2026-07-17. Use current pages when implementing because Azure
schemas and product behavior can change.

## Easy Auth and ARM

- [App Service authentication and authorization overview](https://learn.microsoft.com/azure/app-service/overview-authentication-authorization)
- [Configure App Service or Azure Functions with Microsoft Entra sign-in](https://learn.microsoft.com/azure/app-service/configure-authentication-provider-aad)
- [`Microsoft.Web/sites/config` `authsettingsV2` Bicep reference](https://learn.microsoft.com/azure/templates/microsoft.web/sites/config-authsettingsv2)
- [Work with user identities in App Service authentication](https://learn.microsoft.com/azure/app-service/configure-authentication-user-identities)
- [Work with OAuth tokens in App Service authentication](https://learn.microsoft.com/azure/app-service/configure-authentication-oauth-tokens)
- [Enable diagnostic logging for App Service](https://learn.microsoft.com/azure/app-service/troubleshoot-diagnostic-logs)
- [Manage App Service authentication API and runtime versions](https://learn.microsoft.com/azure/app-service/configure-authentication-api-version)

Documented guarantees used by this skill:

- `allowedApplications` evaluates the v1 `appid` or v2 `azp` client claim.
- Built-in authorization policy failures return 403.
- Allowed applications and allowed principals are ANDed when both exist.
- The API client ID is accepted as its audience; additional Application ID URI
  forms can be configured.
- `/.auth/me` provider token retrieval depends on token store.

## Microsoft Entra tokens and applications

- [Access tokens](https://learn.microsoft.com/entra/identity-platform/access-tokens)
- [Access token claims reference](https://learn.microsoft.com/entra/identity-platform/access-token-claims-reference)
- [Microsoft Graph format application manifest](https://learn.microsoft.com/entra/identity-platform/reference-microsoft-graph-app-manifest)
- [OAuth 2.0 client credentials flow](https://learn.microsoft.com/entra/identity-platform/v2-oauth2-client-creds-grant-flow)
- [Add app roles to an application](https://learn.microsoft.com/entra/identity-platform/howto-add-app-roles-in-apps)
- [Configure an application to trust a managed identity](https://learn.microsoft.com/entra/workload-id/workload-identity-federation-config-app-trust-managed-identity)
- [Grant tenant-wide admin consent](https://learn.microsoft.com/entra/identity/enterprise-apps/grant-admin-consent)
- [Conditional Access overview](https://learn.microsoft.com/entra/identity/conditional-access/overview)

Documented token facts used by this skill:

- v2 access token `aud` is the resource API client ID.
- v1 `appid` and v2 `azp` identify the client application.
- `scp` represents delegated scopes and `roles` represents assigned roles.
- `appidacr` and `azpacr` describe the client authentication method.
- Claims can be absent, so code must not assume every optional claim exists.

## Deployment and hosting

- [Azure Functions Flex Consumption plan](https://learn.microsoft.com/azure/azure-functions/flex-consumption-plan)
- [Create and manage Flex Consumption apps](https://learn.microsoft.com/azure/azure-functions/flex-consumption-how-to)
- [Deploy files to App Service](https://learn.microsoft.com/azure/app-service/deploy-zip)
- [Azure Developer CLI overview](https://learn.microsoft.com/azure/developer/azure-developer-cli/overview)
- [`az account get-access-token`](https://learn.microsoft.com/cli/azure/account#az-account-get-access-token)

Documented Flex facts used by this skill:

- Flex is Linux-based and has region restrictions.
- VNet integration requires `Microsoft.App` registration and
  `Microsoft.App/environments` subnet delegation.
- Flex package deployment uses blob storage.
- Flex does not support deployment slots.

## Empirical boundaries

Official documentation does not enumerate every malformed, expired,
wrong-audience, and caller-policy status combination. It also does not provide
one universal azd, Bicep, package deployment, and Easy Auth sequence for every
plan. The skill labels its controlled status matrix and sequencing as empirical
validation or operational guidance rather than universal guarantees.
