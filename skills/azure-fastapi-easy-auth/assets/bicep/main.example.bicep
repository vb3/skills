param siteName string
param tenantId string
param resourceAppClientId string
param allowedClientApplicationIds string[]

module easyAuth 'easy-auth.bicep' = {
  name: 'easy-auth'
  params: {
    siteName: siteName
    tenantId: tenantId
    resourceAppClientId: resourceAppClientId
    allowedClientApplicationIds: allowedClientApplicationIds
    includeApplicationIdUriAudience: true
    tokenStoreEnabled: false
    forwardProxyConvention: 'NoProxy'
  }
}
