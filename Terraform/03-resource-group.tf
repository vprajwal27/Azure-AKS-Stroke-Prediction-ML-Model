
resource "azurerm_resource_group" "aks_rg" {
  name     = "at-risk-${var.environment}-rg"
  location = "Canada Central" 

  tags = {
    environment = var.environment
    project     = "at-risk-api"
    managed_by  = "terraform"
  }
}
