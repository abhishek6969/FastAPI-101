variable "resource_group_name" {
  type    = string
  default = "rg-fastapi-lirook"
}

variable "kv_id" {
  type    = string
  default = "/subscriptions/bed9c8b2-bb60-492d-92a9-d1641fb7adf8/resourceGroups/remote-backend/providers/Microsoft.KeyVault/vaults/terraform-kv-lirook"
}

variable "location" {
  type    = string
  default = "centralindia"
}

variable "subscription_id" {
  type    = string
  default = "bed9c8b2-bb60-492d-92a9-d1641fb7adf8"
}