// main.bicep - Deploys a Resource Group and an Azure AI Search service within it

// Removed decorator from targetScope - fixes BCP130
targetScope = 'subscription' // Required for creating a Resource Group

// --- Parameters ---
@description('Name for the new Resource Group.')
param resourceGroupName string

@description('Azure region for the new Resource Group and the resources within it.')
param location string = 'westeurope' // Choose a default region

@description('Name for the Azure AI Search service. Must be globally unique.')
param searchServiceName string = 'aisearch-${uniqueString(subscription().id, resourceGroupName)}' // Generate a unique name

@description('The SKU (pricing tier) for the Azure AI Search service.')
@allowed([
  'free'
  'basic'
  'standard'
  'standard2'
  'standard3'
])
param searchServiceSku string = 'basic'

// --- Resource Group Definition ---
@description('Creates the Resource Group.')
resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
}

// --- Module Deployment (AI Search Service) ---
@description('Deploys the Azure AI Search service into the newly created Resource Group.')
module searchDeploy 'search.bicep' = {
  name: 'deployAISearch-${deployment().name}' // Unique name for the module deployment
  scope: rg // Scope this module to the Resource Group created above
  params: {
    searchServiceName: searchServiceName
    location: location // Pass the location to the module
    searchServiceSku: searchServiceSku // Pass the SKU to the module
    // replicaCount and partitionCount use defaults within the module based on SKU
  }
}

// --- Outputs ---
@description('The name of the created Resource Group.')
output rgName string = rg.name

@description('The Resource ID of the deployed Azure AI Search service.')
output searchSvcId string = searchDeploy.outputs.searchServiceId

@description('The Name of the deployed Azure AI Search service.')
output searchSvcName string = searchDeploy.outputs.name

@description('The Primary Admin Key for the Azure AI Search service (sensitive).')
// Removed @secure() decorator - fixes BCP129. Sensitive outputs are handled by Azure.
output searchSvcPrimaryAdminKey string = searchDeploy.outputs.primaryAdminKey
