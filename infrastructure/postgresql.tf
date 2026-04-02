resource "azurerm_postgresql_flexible_server" "fastapi" {
  name                   = "lirook-fastapi"
  resource_group_name    = azurerm_resource_group.fastapi.name
  location               = azurerm_resource_group.fastapi.location
  administrator_login    = "psqladmin"
  administrator_password = data.azurerm_key_vault_secret.fastapi-db.value
  backup_retention_days  = 7
  version                = "18"
  sku_name               = "B_Standard_B1ms"
  storage_mb             = 32768
  storage_tier           = "P4"
  zone                   = 2
  lifecycle {
    ignore_changes = [zone]
  }

}

resource "azurerm_postgresql_flexible_server_database" "example" {
  name      = "fastapi"
  server_id = azurerm_postgresql_flexible_server.fastapi.id
  collation = "en_US.utf8"
  charset   = "UTF8"


}
resource "azurerm_postgresql_flexible_server_firewall_rule" "fastapi" {
  name             = "Allow-all-for-demo"
  server_id        = azurerm_postgresql_flexible_server.fastapi.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "255.255.255.255"
}