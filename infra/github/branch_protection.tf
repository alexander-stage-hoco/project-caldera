# Branch protection rules for the three long-lived branches
# Note: no required_pull_request_reviews — solo developer repo.
# Note: enforce_admins = false — allows admin merge when needed.

resource "github_branch_protection" "main" {
  repository_id = var.github_repository
  pattern       = "main"

  enforce_admins = false

  required_status_checks {
    strict = true
    contexts = [
      "Gate A — Quality",
      "Gate B — Compliance Report",
      "Promotion Policy",
    ]
  }

  allows_force_pushes = false
  allows_deletions    = false
}

resource "github_branch_protection" "release" {
  repository_id = var.github_repository
  pattern       = "release"

  enforce_admins = false

  required_status_checks {
    strict = true
    contexts = [
      "Gate A — Quality",
      "Gate B — Compliance Report",
      "Gate C — Production Smoke",
    ]
  }

  allows_force_pushes = false

  depends_on = [github_branch.release]
}

resource "github_branch_protection" "develop" {
  repository_id = var.github_repository
  pattern       = "develop"

  enforce_admins = false

  required_status_checks {
    strict = true
    contexts = [
      "Gate A — Quality",
    ]
  }

  allows_force_pushes = false

  depends_on = [github_branch.develop]
}
