
resource "azurerm_kubernetes_cluster" "aks_cluster" {
  name                = "${var.environment}-aks"
  location            = azurerm_resource_group.aks_rg.location
  resource_group_name = azurerm_resource_group.aks_rg.name
  dns_prefix          = "${var.environment}-aks"
  kubernetes_version  = data.azurerm_kubernetes_service_versions.current.latest_version

  default_node_pool {
    name                 = "systempool"
    node_count           = var.environment == "prod" ? 2 : 1 # prod gets 2 nodes, staging 1
    vm_size              = "Standard_D2s_v3"                   
    vnet_subnet_id       = azurerm_subnet.aks_subnet.id
    orchestrator_version = data.azurerm_kubernetes_service_versions.current.latest_version
    os_disk_size_gb      = 30
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "azure" # Azure CNI
    load_balancer_sku = "standard"
    service_cidr      = "10.1.0.0/16"
    dns_service_ip    = "10.1.0.10"
  }

  tags = {
    environment = var.environment
    project     = "at-risk-api"
  }
}
