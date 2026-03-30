terraform {
  backend "azurerm" {
    resource_group_name  = "remote-backend"
    storage_account_name = "lirookbackend"
    container_name       = "state-folder"
    key                  = "fastapi.terraform.tfstate"
    # use_azuread_auth   = true # Recommended for secure authentication
  }
}