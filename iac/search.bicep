// search.bicep - Deploys an Azure AI Search service

@description('Name of the Azure AI Search service. Must be globally unique.')
param searchServiceName string

@description('Azure region where the search service will be deployed.')
param location string = resourceGroup().location // Defaults to the location of the resource group

@description('The SKU (pricing tier) for the Azure AI Search service.')
@allowed([
  'free'
  'basic'
  'standard'
  'standard2'
  'standard3'
  // Add other specific SKUs like 'storage_optimized_l1', 'storage_optimized_l2' if needed
])
param searchServiceSku string = 'basic'

@description('The number of replicas for the search service. Not applicable for Free tier.')
param replicaCount int = (searchServiceSku == 'free') ? 1 : 1 // Free tier fixed at 1 replica, default 1 for others

@description('The number of partitions for the search service. Not applicable for Free tier.')
param partitionCount int = (searchServiceSku == 'free') ? 1 : 1 // Free tier fixed at 1 partition, default 1 for others

// --- Azure AI Search Service Resource ---
resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchServiceName
  location: location
  sku: {
    name: searchServiceSku
  }
  properties: {
    replicaCount: replicaCount
    partitionCount: partitionCount
    hostingMode: 'default' // Required property
    // You can configure other properties like publicNetworkAccess, networkRuleSet, encryption, etc. here
    // Example: disabling public access
    // publicNetworkAccess: 'disabled'
  }
}

// --- Outputs ---
@description('The Resource ID of the deployed Azure AI Search service.')
output searchServiceId string = searchService.id

@description('The primary admin key for the Azure AI Search service. Note: Outputting secrets is generally discouraged for production systems.')
// Updated to use resource symbol reference - addresses linter warning BCP081
// Note: The linter will still warn about outputting secrets (outputs-should-not-contain-secrets) - this is a design choice here.
output primaryAdminKey string = searchService.listAdminKeys().primaryKey

@description('The name of the Azure AI Search service.')
output name string = searchService.name
