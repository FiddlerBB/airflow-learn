terraform {
  required_version = ">= 1.9.4"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.55.0"
    }
  }
}

# Configure AWS provider
provider "aws" {
  region = var.aws_region
}


terraform {
  backend "s3" {
    bucket         = "terraform-state-bucket-gold-scrape"
    key            = "airflow-terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks" # Optional: For state locking
    encrypt        = true
  }
}

