targetScope = 'subscription'

@minLength(1)
@maxLength(64)
param environmentName string

@minLength(1)
param location string

param entraTenantId string
param resourceAppClientId string
param allowedClientApplicationIdsCsv string

var tags = {
  'azd-env-name': environmentName
}

resource resourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: '${environmentName}-rg'
  location: location
  tags: tags
}

module app './app.bicep' = {
  name: 'fastapi-flex'
  scope: resourceGroup
  params: {
    environmentName: environmentName
    location: location
    tags: tags
    entraTenantId: entraTenantId
    resourceAppClientId: resourceAppClientId
    allowedClientApplicationIdsCsv: allowedClientApplicationIdsCsv
  }
}

output AZURE_LOCATION string = location
output AZURE_RESOURCE_GROUP string = resourceGroup.name
output SERVICE_API_NAME string = app.outputs.functionAppName
output API_ENDPOINT string = app.outputs.apiEndpoint
