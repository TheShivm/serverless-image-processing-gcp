terraform {
  # Single-operator project: back up this local state outside the repository.
  backend "local" {
    path = "terraform.tfstate"
  }
}
