using './main.bicep'

// Values stay in this terminal's environment; never compile this file to a saved JSON with real secrets.
param databasePassword = readEnvironmentVariable('GS_AZURE_DB_PASSWORD')
param secretKey = readEnvironmentVariable('GS_AZURE_SECRET_KEY')
