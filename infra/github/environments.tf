# GitHub Environments for protected deployments
# Secrets (ANTHROPIC_API_KEY, HCLOUD_TOKEN, SSH_PRIVATE_KEY) are added manually in GitHub UI

# Resolve reviewer user IDs from usernames
data "github_user" "llm_eval_reviewers" {
  for_each = toset(var.llm_eval_reviewers)
  username = each.value
}

data "github_user" "cloud_reviewers" {
  for_each = toset(var.cloud_reviewers)
  username = each.value
}

resource "github_repository_environment" "llm_eval" {
  repository  = var.github_repository
  environment = "llm-eval"

  dynamic "reviewers" {
    for_each = length(var.llm_eval_reviewers) > 0 ? [1] : []
    content {
      users = [for u in data.github_user.llm_eval_reviewers : u.id]
    }
  }

  deployment_branch_policy {
    protected_branches     = true
    custom_branch_policies = false
  }
}

resource "github_repository_environment" "cloud" {
  repository  = var.github_repository
  environment = "cloud"

  dynamic "reviewers" {
    for_each = length(var.cloud_reviewers) > 0 ? [1] : []
    content {
      users = [for u in data.github_user.cloud_reviewers : u.id]
    }
  }

  deployment_branch_policy {
    protected_branches     = true
    custom_branch_policies = false
  }
}
