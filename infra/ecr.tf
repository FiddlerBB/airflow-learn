resource "aws_ecr_repository" "airflow_build" {
  name = "airflow-build"
  
  image_scanning_configuration {
    scan_on_push = true
  }
}
