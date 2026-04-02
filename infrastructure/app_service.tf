

resource "azurerm_service_plan" "fastapi" {
  name                = "example"
  resource_group_name = azurerm_resource_group.fastapi.name
  location            = azurerm_resource_group.fastapi.location
  os_type             = "Linux"
  sku_name            = "B1"
}

resource "azurerm_linux_web_app" "fastapi" {
  name                = "fastapi-lirook"
  resource_group_name = azurerm_resource_group.fastapi.name
  location            = azurerm_service_plan.fastapi.location
  service_plan_id     = azurerm_service_plan.fastapi.id



  site_config {
    application_stack {
      docker_image_name        = "lirook6969/kodekloudproject-api:latest"
      docker_registry_url      = "https://index.docker.io"
      docker_registry_username = "lirook6969"
      docker_registry_password = data.azurerm_key_vault_secret.fastapi-dockerpass.value
    }

  }
  app_settings = {
    "ACCESS_TOKEN_EXPIRE_MINUTES" = "30"
    "DATABASE_DRIVER"             = "postgresql"
    "DATABASE_HOSTNAME"           = "lirook-fastapi.postgres.database.azure.com"
    "DATABASE_NAME"               = "fastapi"
    "DATABASE_PASSWORD"           = data.azurerm_key_vault_secret.fastapi-db.value
    "DATABASE_PORT"               = "5432"
    "DATABASE_USERNAME"           = "psqladmin"
    "SECRET_KEY"                  = data.azurerm_key_vault_secret.fastapi-apikey.value
    "ALGORITHM"                   = "HS256"
    "WEBSITES_PORT"               = 8000
  }
}