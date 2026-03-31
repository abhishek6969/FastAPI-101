

resource "azurerm_service_plan" "fastapi" {
  name                = "example"
  resource_group_name = azurerm_resource_group.fastapi.name
  location            = azurerm_resource_group.fastapi.location
  os_type             = "Linux"
  sku_name            = "F1"
}

resource "azurerm_linux_web_app" "fastapi" {
  name                = "fastapi-lirook"
  resource_group_name = azurerm_resource_group.fastapi.name
  location            = azurerm_service_plan.fastapi.location
  service_plan_id     = azurerm_service_plan.fastapi.id
  
  

  site_config {
    application_stack {
      python_version = "3.13"
      
    }
    always_on = false
    app_command_line = "gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.main:app"
    
    
    
  }
  app_settings                    = {
    "ACCESS_TOKEN_EXPIRE_MINUTES" = "30"
    "DATABASE_DRIVER"             = "postgresql"
    "DATABASE_HOST"               = "lirook-fastapi.postgres.database.azure.com"
    "DATABASE_NAME"               = "fastapi"
    "DATABASE_PASSWORD"           = data.azurerm_key_vault_secret.fastapi-db.value
    "DATABASE_PORT"               = "5432"
    "DATABASE_USER"               = "psqladmin"
    "SECRET_KEY"                   = data.azurerm_key_vault_secret.fastapi-apikey.value
    "ALGORITHM"                   = "HS256"
  }
}