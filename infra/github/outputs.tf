output "branches" {
  description = "Long-lived branches managed by Terraform"
  value = {
    develop = github_branch.develop.branch
    release = github_branch.release.branch
  }
}

output "environments" {
  description = "GitHub Environments managed by Terraform"
  value = {
    llm_eval = github_repository_environment.llm_eval.environment
    cloud    = github_repository_environment.cloud.environment
  }
}

output "protected_branches" {
  description = "Branches with protection rules"
  value       = ["main", "develop", "release"]
}
