@description('Name of an existing Azure Functions or App Service site.')
param siteName string

@description('Microsoft Entra workforce tenant ID.')
param tenantId string

@description('Client ID of the resource API app registration.')
param resourceAppClientId string

@description('Client IDs allowed to call the resource API.')
param allowedClientApplicationIds string[]

@description('Also accept api://<resource app client ID> for the same API.')
param includeApplicationIdUriAudience bool = true

@description('Enable /.auth/me and provider token storage only when required.')
param tokenStoreEnabled bool = false

@description('Proxy convention for direct, standard proxy, or custom proxy ingress.')
@allowed([
  'NoProxy'
  'Standard'
  'Custom'
])
param forwardProxyConvention string = 'NoProxy'

@description('Custom proxy header carrying the original host. Used only when set.')
param forwardProxyCustomHostHeaderName string = ''

@description('Custom proxy header carrying the original protocol. Used only when set.')
param forwardProxyCustomProtoHeaderName string = ''

var allowedAudiences = includeApplicationIdUriAudience
  ? [
      resourceAppClientId
      'api://${resourceAppClientId}'
    ]
  : [
      resourceAppClientId
    ]

var forwardProxySettings = union(
  {
    convention: forwardProxyConvention
  },
  empty(forwardProxyCustomHostHeaderName)
    ? {}
    : {
        customHostHeaderName: forwardProxyCustomHostHeaderName
      },
  empty(forwardProxyCustomProtoHeaderName)
    ? {}
    : {
        customProtoHeaderName: forwardProxyCustomProtoHeaderName
      }
)

var azureActiveDirectoryValidation = union(
  {
    allowedAudiences: allowedAudiences
  },
  length(allowedClientApplicationIds) > 0
    ? {
        defaultAuthorizationPolicy: {
          allowedApplications: allowedClientApplicationIds
        }
      }
    : {}
)

resource site 'Microsoft.Web/sites@2024-04-01' existing = {
  name: siteName
}

resource authSettings 'Microsoft.Web/sites/config@2024-04-01' = {
  parent: site
  name: 'authsettingsV2'
  properties: {
    platform: {
      enabled: true
      runtimeVersion: '~1'
    }
    globalValidation: {
      requireAuthentication: true
      unauthenticatedClientAction: 'Return401'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          clientId: resourceAppClientId
          openIdIssuer: '${environment().authentication.loginEndpoint}${tenantId}/v2.0'
        }
        validation: azureActiveDirectoryValidation
      }
    }
    httpSettings: {
      requireHttps: true
      routes: {
        apiPrefix: '/.auth'
      }
      forwardProxy: forwardProxySettings
    }
    login: {
      tokenStore: {
        enabled: tokenStoreEnabled
      }
    }
  }
}
