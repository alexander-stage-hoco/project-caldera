variable "github_owner" {
  description = "GitHub organization or username that owns the repository"
  type        = string
}

variable "github_repository" {
  description = "Repository name (without owner prefix)"
  type        = string
}

variable "llm_eval_reviewers" {
  description = "GitHub usernames required to approve llm-eval environment deployments"
  type        = list(string)
  default     = []
}

variable "cloud_reviewers" {
  description = "GitHub usernames required to approve cloud environment deployments"
  type        = list(string)
  default     = []
}
