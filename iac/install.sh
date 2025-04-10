# Install Ollama
brew install ollama

# Pull the embedding model
ollama pull bge-m3  

# Serve the embedding model
ollama serve bge-m3

# Login to Azure (if not already)
az login

# Set the subscription context (if you have multiple)
az account set --subscription "YOUR SUBSCRIPTION NAME OR ID"

# Define deployment parameters
RG_NAME="Contoso-Dev-Swe"          # Choose your resource group name
LOCATION="swedencentral"            # Choose your Azure region
SEARCH_SVC_NAME="contosoaisvc$RANDOM" # Choose a globally unique name or use the default from main.bicep
SEARCH_SKU="basic"                 # Choose desired SKU (free, basic, standard...)
DEPLOYMENT_NAME="createRgAndSearch" # Name for the deployment operation

# Deploy at the subscription scope
az deployment sub create \
  --name $DEPLOYMENT_NAME \
  --location $LOCATION \
  --template-file main.bicep \
  --parameters resourceGroupName=$RG_NAME \
               location=$LOCATION \
               searchServiceName=$SEARCH_SVC_NAME \
               searchServiceSku=$SEARCH_SKU