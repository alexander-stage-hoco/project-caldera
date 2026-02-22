# Create long-lived branches from main

resource "github_branch" "develop" {
  repository    = var.github_repository
  branch        = "develop"
  source_branch = "main"
}

resource "github_branch" "release" {
  repository    = var.github_repository
  branch        = "release"
  source_branch = "main"
}
