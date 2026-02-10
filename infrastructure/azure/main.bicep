// ============================================================
// Azure Infrastructure for Salesforce Analytics Platform
// Bicep template for Function App, Storage, App Service
// ============================================================

@description('Deployment environment')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Function App SKU')
param functionAppSku string = 'Y1'

var projectName = 'sfanalytics'
var uniqueSuffix = uniqueString(resourceGroup().id)
var storageAccountName = '${projectName}${uniqueSuffix}'
var functionAppName = '${projectName}-func-${environment}'
var appServicePlanName = '${projectName}-plan-${environment}'
var appInsightsName = '${projectName}-insights-${environment}'
var dashboardAppName = '${projectName}-dashboard-${environment}'

// --- Storage Account ---

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    encryption: {
      services: {
        blob: {
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
  tags: {
    Project: 'SalesforceAnalytics'
    Environment: environment
  }
}

// Blob container for analytics data
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

resource analyticsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'salesforce-data'
  properties: {
    publicAccess: 'None'
  }
}

// --- Application Insights ---

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    RetentionInDays: 30
  }
  tags: {
    Project: 'SalesforceAnalytics'
    Environment: environment
  }
}

// --- App Service Plan (shared by Function App and Dashboard) ---

resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: functionAppSku
    tier: functionAppSku == 'Y1' ? 'Dynamic' : 'Standard'
  }
  properties: {
    reserved: true  // Linux
  }
  tags: {
    Project: 'SalesforceAnalytics'
    Environment: environment
  }
}

// --- Azure Function App ---

resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      pythonVersion: '3.11'
      linuxFxVersion: 'PYTHON|3.11'
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'AZURE_STORAGE_CONNECTION_STRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'AZURE_CONTAINER'
          value: 'salesforce-data'
        }
        {
          name: 'USE_MOCK_DATA'
          value: 'true'
        }
      ]
    }
  }
  tags: {
    Project: 'SalesforceAnalytics'
    Environment: environment
  }
}

// --- Web App for Dashboard ---

resource dashboardApp 'Microsoft.Web/sites@2023-01-01' = {
  name: dashboardAppName
  location: location
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      pythonVersion: '3.11'
      linuxFxVersion: 'PYTHON|3.11'
      appCommandLine: 'gunicorn --bind=0.0.0.0 --timeout 600 src.dashboard.app:app'
      appSettings: [
        {
          name: 'USE_MOCK_DATA'
          value: 'true'
        }
        {
          name: 'AZURE_STORAGE_CONNECTION_STRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'DASHBOARD_DEBUG'
          value: 'false'
        }
      ]
    }
  }
  tags: {
    Project: 'SalesforceAnalytics'
    Environment: environment
  }
}

// --- Outputs ---

output storageAccountName string = storageAccount.name
output functionAppName string = functionApp.name
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output dashboardUrl string = 'https://${dashboardApp.properties.defaultHostName}'
output appInsightsKey string = appInsights.properties.InstrumentationKey
