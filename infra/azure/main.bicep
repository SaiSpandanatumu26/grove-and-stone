targetScope = 'resourceGroup'

@description('Choose a region supported by the subscription before deployment.')
param location string = resourceGroup().location
@minLength(3)
@maxLength(18)
param prefix string = 'grove-stone'
@secure()
@minLength(16)
param databasePassword string
@secure()
@minLength(32)
param secretKey string
@description('Sample preview amounts; replace with approved business values for real sales.')
param shippingFee string = '49'
param freeShippingThreshold string = '999'

var suffix = uniqueString(resourceGroup().id)
var appName = '${prefix}-${suffix}'
var dbName = '${prefix}-pg-${suffix}'
var databaseUser = 'groveadmin'
var tags = { project: 'Grove and Stone', environment: 'review' }

resource network 'Microsoft.Network/virtualNetworks@2024-05-01' = {
  name: '${prefix}-vnet'
  location: location
  tags: tags
  properties: {
    addressSpace: { addressPrefixes: ['10.42.0.0/16'] }
    subnets: [
      {
        name: 'web'
        properties: {
          addressPrefix: '10.42.1.0/26'
          delegations: [{ name: 'web', properties: { serviceName: 'Microsoft.Web/serverFarms' } }]
        }
      }
      {
        name: 'database'
        properties: {
          addressPrefix: '10.42.2.0/27'
          delegations: [{ name: 'postgres', properties: { serviceName: 'Microsoft.DBforPostgreSQL/flexibleServers' } }]
        }
      }
    ]
  }
}

resource dns 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: '${prefix}.private.postgres.database.azure.com'
  location: 'global'
  tags: tags
}
resource dnsLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: dns
  name: '${prefix}-link'
  location: 'global'
  properties: { registrationEnabled: false, virtualNetwork: { id: network.id } }
}

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: dbName
  location: location
  tags: tags
  sku: { name: 'Standard_B1ms', tier: 'Burstable' }
  properties: {
    version: '17'
    administratorLogin: databaseUser
    administratorLoginPassword: databasePassword
    authConfig: { passwordAuth: 'Enabled', activeDirectoryAuth: 'Disabled' }
    storage: { storageSizeGB: 32, autoGrow: 'Disabled' }
    backup: { backupRetentionDays: 7, geoRedundantBackup: 'Disabled' }
    highAvailability: { mode: 'Disabled' }
    network: {
      delegatedSubnetResourceId: '${network.id}/subnets/database'
      privateDnsZoneArmResourceId: dns.id
      publicNetworkAccess: 'Disabled'
    }
  }
  dependsOn: [dnsLink]
}
resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  parent: postgres
  name: 'grove_stone'
  properties: { charset: 'UTF8', collation: 'en_US.utf8' }
}

resource plan 'Microsoft.Web/serverfarms@2024-11-01' = {
  name: '${prefix}-plan'
  location: location
  tags: tags
  kind: 'linux'
  sku: { name: 'B1', tier: 'Basic', capacity: 1 }
  properties: { reserved: true }
}
resource site 'Microsoft.Web/sites@2024-11-01' = {
  name: appName
  location: location
  tags: tags
  kind: 'app,linux'
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    virtualNetworkSubnetId: '${network.id}/subnets/web'
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.14'
      appCommandLine: 'bash infra/azure/start.sh'
      alwaysOn: true
      minTlsVersion: '1.2'
      scmMinTlsVersion: '1.2'
      ftpsState: 'Disabled'
      healthCheckPath: '/api/v1/health'
    }
  }
}
resource ftpPolicy 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2024-11-01' = {
  parent: site
  name: 'ftp'
  properties: { allow: false }
}
resource scmPolicy 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2024-11-01' = {
  parent: site
  name: 'scm'
  properties: { allow: false }
}
resource settings 'Microsoft.Web/sites/config@2024-11-01' = {
  parent: site
  name: 'appsettings'
  properties: {
    SCM_DO_BUILD_DURING_DEPLOYMENT: 'true'
    DATABASE_URL: 'postgresql+psycopg://${databaseUser}:${uriComponent(databasePassword)}@${postgres.properties.fullyQualifiedDomainName}:5432/${database.name}?sslmode=require'
    SECRET_KEY: secretKey
    WEB_DIST_DIR: 'web'
    PUBLIC_API_URL: 'https://${site.properties.defaultHostName}'
    CORS_ORIGINS: 'https://${site.properties.defaultHostName}'
    PAYMENT_BACKEND: 'disabled'
    CONTACT_BACKEND: 'disabled'
    SHIPPING_FEE: shippingFee
    FREE_SHIPPING_THRESHOLD: freeShippingThreshold
    RATELIMIT_STORAGE_URI: 'memory://'
  }
}

output appName string = site.name
output websiteUrl string = 'https://${site.properties.defaultHostName}'
output apiUrl string = 'https://${site.properties.defaultHostName}/api/v1'
output postgresName string = postgres.name
