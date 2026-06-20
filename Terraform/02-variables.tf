#   terraform apply -var="environment=staging"
#   terraform apply -var="environment=prod"


variable "environment" {
  type        = string
  description = "Environment name: staging or prod"
}
