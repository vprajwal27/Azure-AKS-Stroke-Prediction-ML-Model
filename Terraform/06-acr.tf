
resource "azurerm_container_registry" "acr" {
  name                = "atrisk${var.environment}CHANGEME" 
  resource_group_name = azurerm_resource_group.aks_rg.name
  location            = azurerm_resource_group.aks_rg.location
  sku                 = "Basic"
  admin_enabled       = false
}

# Grant the AKS kubelet identity permission to pull images from this ACR

resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                            = azurerm_container_registry.acr.id
  role_definition_name             = "AcrPull"
  principal_id                     = azurerm_kubernetes_cluster.aks_cluster.kubelet_identity[0].object_id
  skip_service_principal_aad_check = true
}
