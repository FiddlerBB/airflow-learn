include .env
export

TAG := 1.0.0
# ECR_ARN := $(TF_VAR_AWS_ACCOUNT_ID).dkr.ecr.$(TF_VAR_REGION).amazonaws.com
TF_BASE_PATH := infra

build:
	@echo "Building image $(IMAGE_NAME)"
# @docker build -t $(ECR_ARN)/$(IMAGE_NAME) .
	@docker build -t $(IMAGE_NAME) .

# run: 
# 	@echo "Running image $(ECR_ARN)/$(IMAGE_NAME)"
# 	@docker run --rm -it -p 8083:8080 \
# 	$(ECR_ARN)/$(IMAGE_NAME) main.lambda_handler

login-ecr:
	@echo "Login into ECR"
	@aws ecr get-login-password --region $(TF_VAR_REGION) | docker login --username AWS --password-stdin $(ECR_ARN)

push: login-ecr
	@echo "Push image to ECR"
	@docker tag $(IMAGE_NAME):latest $(ECR_ARN)/$(IMAGE_NAME):latest
	@docker push $(ECR_ARN)/$(IMAGE_NAME)

pull: login-ecr
	@echo "Pull image from ECR"
	@docker pull $(ECR_ARN)/$(IMAGE_NAME):latest


infra-init:
	@cd $(TF_BASE_PATH) && \
	terraform init -migrate-state

infra-plan:
	@echo $(TF_VAR_TOPIC_NAME)
	@cd $(TF_BASE_PATH) && \
	terraform plan

infra-apply:
	@cd $(TF_BASE_PATH) && \
		terraform apply

infra-destroy:
	@cd $(TF_BASE_PATH) && \
	terraform destroy