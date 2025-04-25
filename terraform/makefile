# make terraform project_name="my_project" region="us-west-2"
# Load the .env file

GLOBAL_PYTHON = $(DEFAULT_PYTHON)
TF_VAR_REGION =
TF_VAR_BUCKET =
TF_VAR_ENVIRONMENT =

clean:
	@echo "\nCleaning up the terraform modules directory"
	- [ -d .terraform/modules ] && rm -r .terraform/modules
	- [ -f .terraform/terraform.tfstate ] && rm .terraform/terraform.tfstate

create_env: 
	@if [ "$(OS)" = "Windows_NT" ]; then \
		pip3 install pipenv; \
	elif [ "$(shell uname)" = "Darwin" ]; then \
		brew install pipenv; \
	fi
	@echo "\nInstalling Python dependencies"
	pipenv install --dev

# Require a confirmation that the .env file is ready
require_confirmation_env: create_env
	@echo "\nDid you prepare your .env file in the root directory with all of the vars from .env.example?"
	@read -p "Type 'yes' to continue: " response; \
	if [ "$$response" != "yes" ]; then \
		make failure-action; \
	fi

cleanup_env_files: require_confirmation_env
	@output=$$(pipenv run python scripts/clean_env.py); \


set_config_variables: cleanup_env_files
	@echo "\nType the region you want to deploy to in format us-region-#. EXAMPLE us-west-2" ; \
	read -p "Enter region: " region_response; \
	TF_VAR_REGION=$$region_response; \
	echo "\nTF_VAR_REGION=$$region_response" >> ../.env && \
	echo "region=\"$$region_response\"" > backend.conf && \
	export TF_VAR_REGION

	@echo "\nType the environment you want to use for Terraform either dev or prod and Enter." ; \
	read -p "Enter environment name: " env_response; \
	TF_VAR_ENVIRONMENT=$$env_response; \
	echo "TF_VAR_ENVIRONMENT=$$env_response" >> ../.env && \
	export TF_VAR_ENVIRONMENT

	@echo "\nType the name of the S3 bucket you want to use for Terraform files and press Enter. EXAMPLE my-terraform-bucket" ; \
	read -p "Enter bucket name: " bucket_response; \
	TF_VAR_BUCKET=$$bucket_response; \
	echo "TF_VAR_BUCKET=$$bucket_response" >> ../.env && \
	echo "bucket=\"$$bucket_response_$$env_response\"" >> backend.conf && \
	export TF_VAR_BUCKET

	@echo "\nType the AWS profile you want to use for Terraform EXACTLY, without brackets, and Enter. Example: 123456789_ProfileName" ; \
	read -p "Enter profile: " profile_response; \
	TF_VAR_AWS_PROFILE=$$profile_response; \
	echo "TF_VAR_AWS_PROFILE=$$profile_response" >> ../.env && \
	echo "profile=\"$$profile_response\"" >> backend.conf && \
	export TF_VAR_AWS_PROFILE

	@echo "\n"
	@curl ifconfig.me
	@echo "\nType the first 3 numbers of the IP printed above, in format x.x.x and press Enter. EXAMPLE 10.123.123" ;\
	read -p "Enter first 3 number x.x.x: " ip_response; \
    TF_VAR_MY_IP_FIRST_THREE_BLOCKS=$$ip_response; \
    echo "TF_VAR_MY_IP_FIRST_THREE_BLOCKS=$$TF_VAR_MY_IP_FIRST_THREE_BLOCKS" >> ../.env


enter_temp_vars: set_config_variables
	echo "IS_LOCAL=False" >> ../.env

# Make the backend config file for terraform
backend_config: enter_temp_vars
	echo 'key="boardgamegeek.tfstate"' >> backend.conf

# A target that runs the Python script and checks the output
terraform: backend_config
	@echo "\nRunning Python script to validate entries"
	@output=$$(pipenv run python scripts/validate.py $(TF_VAR_BUCKET) $(TF_VAR_REGION)) || { echo "Script execution failed"; exit 1; }; \
	echo "\nOutput from script: $$output"; \
	if [ "$$output" = "validated" ]; then \
		echo "Python script returned success"; \
		make cleanup_superfluous_files; \
	else \
		echo "Python script returned failure"; \
		make failure-action; \
	fi

install_state_file_bucket:
	cd s3_state_bucket && \
	\[ -f .terraform.lock.hcl \] && rm .terraform.lock.hcl && \
	pipenv run terraform init -backend-config ../backend.conf && \
	pipenv run terraform apply && \
	cd .. && \
	cd ..

# setup main project
setup_boardgamegeek: 
	pipenv run terraform init -backend-config backend.conf && \
	pipenv run terraform apply

# Clean up garbage files
cleanup_superfluous_files: setup_boardgamegeek
	@echo "\nCleaning up garbage files"
	find . -type f -name "*.DS_Store" -delete
	find . -type f -name '*!lambda_function.zip' -delete
	echo "PYTHONPATH=." >> ../.env

copy_yml_to_ec2: cleanup_superfluous_files
	@echo "\nCopying the docker-compose.yml file to the EC2 instance"
	
failure-action:
	@echo "\nScript was not ready to run Terraform. Running cleanup and exiting, do not interrupt..."
	@output=$$(pipenv run python scripts/clean_env.py); \
	exit 1

update:
	@echo "\nUpdating Terraform install"
	make cleanup_superfluous_files; \




