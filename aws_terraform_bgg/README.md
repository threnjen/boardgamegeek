# terraform_modules
Set up the AWS tech stack for boardgamegeek to run on the cloud.

You must have administration level privileges to create these resources in AWS, or at least create/destroy privileges in the following areas: IAM, VPC. S3, ECR, ECS, Lambda

## Step 01 - Install Terraform and Make

Terraform installation:
https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli

Make installation:
Mac OS generally has make. For Windows:

#### Step 02 .env file

Use the .env example file to create a file called `.env` with all of the Environment vars that your project needs, as laid out in env.example. All of these variables must be specified or the project will fail. 

## Step 03 - Open command line to boardgamegeek_terraform directory

`make terraform`
Follow all prompts exactly as written.

!!!!! YOU WILL HAVE ERRORS AT THE LAST STEP. THIS IS EXPECTED !!!!!
There's a bit of a cart-horse issue at this step.

It's time to set up your GitHub CI/CD so that your project files write to the AWS ECR. The AWS resources cannot complete setup until the project has been uploaded.

Open up the MAIN boardgamegeek project directory and complete all steps through the  "Set up GitHub Secrets" section, including pushing to the repo so that all of the projects deploy to their respective locations on AWS.

## Step 04 - Run the project again to finish creating the resources

`make setup_boardgamegeek`
Follow all prompts exactly as written.

## My IP Address changed! How do I update it in AWS?

Run the following commands:
`cd modules/vpc`
`curl ifconfig.me`
Note down the first 3 numbers in the ip block x.x.x

Run in order:
- `terraform init -backend-config vpc_backend.conf`
- `terraform apply`

Wait for the evaluation to prompt you to proceed. Does everything look ok?
`yes`
