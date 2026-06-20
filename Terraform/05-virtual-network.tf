
# separate VNets in separate resource groups 
# So ["10.0.1.0/24"] address space for both Vnets, but they exist in diff resource group


resource "azurerm_virtual_network" "aks_vnet" {
  name                = "${var.environment}-vnet"
  location            = azurerm_resource_group.aks_rg.location
  resource_group_name = azurerm_resource_group.aks_rg.name
  address_space       = ["10.0.0.0/16"] 
}

resource "azurerm_subnet" "aks_subnet" {
  name                 = "${var.environment}-aks-subnet"
  resource_group_name  = azurerm_resource_group.aks_rg.name
  virtual_network_name = azurerm_virtual_network.aks_vnet.name
  address_prefixes     = ["10.0.1.0/24"] 
}
