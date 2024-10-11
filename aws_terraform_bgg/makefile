# make terraform project_name="my_project" region="us-west-2"
# Load the .env file

GLOBAL_PYTHON = $(DEFAULT_PYTHON)
TF_VAR_REGION =
TF_VAR_BUCKET =

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
require_confirmation_env:  
	@echo "\nDid you prepare your .env file in the root directory with all of the vars from .env.example?"
	@read -p "Type 'yes' to continue: " response; \
	if [ "$$response" != "yes" ]; then \
		make failure-action; \
	fi

cleanup_env_files: require_confirmation_env
	@output=$$(pipenv run python scripts/clean_env.py); \

get_region: cleanup_env_files
	@echo "\nType the region you want to deploy to in format us-region-#. EXAMPLE us-west-2" ; \
	read -p "Enter region: " response; \
	TF_VAR_REGION=$$response; \
	echo "TF_VAR_REGION=$$response" >> .env && \
	echo "region=\"$$response\"" > backend.conf && \
	echo "region=\"$$response\"" > modules/vpc/vpc_backend.conf && \
	export TF_VAR_REGION

get_terraform_bucket: get_region
	@echo "\nType the name of the S3 bucket you want to use for Terraform files and press Enter. EXAMPLE my-terraform-bucket" ; \
	read -p "Enter bucket name: " response; \
	TF_VAR_BUCKET=$$response; \
	echo "TF_VAR_BUCKET=$$response" >> .env && \
	echo "bucket=\"$$response\"" >> backend.conf && \
	echo "bucket=\"$$response\"" >> modules/vpc/vpc_backend.conf && \
	echo "key=\"vpc.tfstate\"" >> modules/vpc/vpc_backend.conf && \
	export TF_VAR_BUCKET

get_current_ip: get_terraform_bucket
	@echo "\n"
	@curl ifconfig.me
	@echo "\nType the first 3 numbers of the IP printed above, in format x.x.x and press Enter. EXAMPLE 10.123.123" ;\
	read -p "Enter first 3 number x.x.x: " response; \
    TF_VAR_MY_IP_FIRST_THREE_BLOCKS=$$response; \
    echo "TF_VAR_MY_IP_FIRST_THREE_BLOCKS=$$TF_VAR_MY_IP_FIRST_THREE_BLOCKS" >> .env

# Make the backend config file for terraform
backend_config: get_current_ip
	echo 'key="boardgamegeek.tfstate"' >> backend.conf

# A target that runs the Python script and checks the output
terraform: backend_config
	@echo "\nRunning Python script to validate project name and region"
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
	cd modules/s3_state_bucket && \
	pipenv run terraform init && \
	pipenv run terraform apply && \
	cd .. && \
	cd ..

setup_vpc: install_state_file_bucket
	cd modules/vpc && \
	pipenv run terraform init -backend-config vpc_backend.conf && \
	pipenv run terraform apply && \
	cd .. && \
	cd ..

# setup main project
setup_boardgamegeek: setup_vpc
	pipenv run terraform init -backend-config backend.conf && \
	pipenv run terraform apply

# Clean up garbage files
cleanup_superfluous_files: setup_boardgamegeek
	@echo "\nCleaning up garbage files"
	find . -type f -name "*.DS_Store" -delete
	find . -type f -name '*!lambda_function.zip' -delete


failure-action:
	@echo "\nScript was not ready to run Terraform. Running cleanup and exiting, do not interrupt..."
	@output=$$(pipenv run python scripts/clean_env.py); \
	exit 1






