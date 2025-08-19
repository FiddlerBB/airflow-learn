variable "aws_region" {
  description = "Region for AWS"
  type        = string
  default     = "us-east-1"
}

variable "EMAIL_SUB" {
  description = "subcribe email"
  type = string
}

variable "AWS_ACCOUNT_ID" {
  description = "account id"
  type = string
}

# variable "IMAGE_URI" {
#   description = "image uri"
#   type = string
# }