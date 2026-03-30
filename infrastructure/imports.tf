data "azurerm_key_vault_secret" "fastapi-apikey" {
  name         = "SECRET-KEY"
  key_vault_id = "/subscriptions/bed9c8b2-bb60-492d-92a9-d1641fb7adf8/resourceGroups/remote-backend/providers/Microsoft.KeyVault/vaults/terraform-kv-lirook"
}

data "azurerm_key_vault_secret" "fastapi-db" {
  name         = "DATABASE-PASSWORD"
  key_vault_id = "/subscriptions/bed9c8b2-bb60-492d-92a9-d1641fb7adf8/resourceGroups/remote-backend/providers/Microsoft.KeyVault/vaults/terraform-kv-lirook"
}

