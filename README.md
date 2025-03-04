# Boardgamegeek

All projects should be run from within the primary `boardgamegeek` directory or relative paths will be a problem.
This repo was created and produced for Mac. The Terraform makefile will run on Mac OS. Support for Windows is unknown.

## Utilized Tech Stack
- Makefile and Terraform to create AWS resources
- Pipenv for environment management
- Docker for project containerization
- GitHub Actions CI/CD for automated AWS deployment
- Resources running on Lambda, Fargate ECS, and EC2
- Project orchestrated and parallelized by Dagster in Fargate ECS container
- S3 storage with Athena/Glue data querying
- DynamoDB key/value store
- Web form automation with Selenium
- Vector DB with Weaviate, hosted on-demand on EC2 server
- Vector embeddings API from Hugging face
- Retrieval Augmented Generation with OpenAI API

## Project Requirements

AWS is required for this project to run as presented. Running on the cloud is not a free service. The authors of this repo are not responsible for any costs incurred by your usage of AWS services.

You must have administration level privileges to create these resources in AWS, or at least create/destroy privileges in the following areas: IAM, VPC. S3, ECR, ECS, Lambda

This project uses Pipenv as its environment manager. Documentation on pipenv is outside the scope of this repo.

## Project Order

Most steps in this project are explicitly dependent on a prior step. Dependencies are noted and explained.

<!-- ## Creating a key pair in AWS

Terraform cannot be used to create your security key in AWS, which you will need to create and connect to the retrieval augmented generation server that is created on EC2. To manually create this key, go to the *EC2* area of AWS and select *Key Pairs* at left. Create a new key and name it "weaviate-ec2" with the default RSA key-pair type and .pem file format. This key will automatically be downloaded to your machine in the Downloads folder. Move it to the ~.ssh/ folder. Then run `chmod 400 ~/.ssh/weaviate-ec2.pem` to make the key write-protected. -->

## Install Terraform

Terraform installation:
https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli

### Set up .env file

A `.env` must be made in the project root directory. 

Copy in the variables from `env.example`:
- Mac: `cp .env.example .env`
- Windows: `stuff`

Prefilled .env vars should be left alone.

Instructions for non-prefilled .env vars:
- S3_SCRAPER_BUCKET= The S3 bucket where you will store your scraper data. This will be created.
- TF_VAR_S3_SCRAPER_BUCKET= This is the SAME value as S3_SCRAPER_BUCKET. Yes, both are needed.
- BGG_USERNAME= your BGG username
- BGG_PASSWORD= your bgg password
- OPENAI_API_KEY= your openapi key. You only need this if you intend to run the RAG modules. You'll need to load your OpenAPI account with some funds - $10 should suffice.
- HUGGINGFACE_APIKEY= your openapi key. You only need this if you intend to run the RAG modules. 
- TF_VAR_GITHUB_USER_NAME= your github username


### Make your AWS resources

EXPORT YOUR AWS KEYS. How you do this is outside of the scope of the repo.

CD to the `aws_terraform_bgg` directory
`make terraform`
Follow all prompts exactly as written.
When prompted to type yes, type yes :)

!!!!! YOU WILL HAVE ERRORS AT THE LAST STEP. THIS IS EXPECTED !!!!! Specifically: `Error: creating Lambda Function (bgg_boardgame_file_retrieval)`
There's a bit of a cart-horse issue at this step.

It's time to set up your GitHub CI/CD so that your project files write to the AWS ECR. The AWS resources cannot complete setup until the project has been uploaded.

### Set up GitHub Secrets for your project

Go to Github, to your repo. Create two Secrets in the Secrets area of your project fork before continuing. Hint: Go to Repo, Settings along top of repo, "Secrets and Variables" along left menu, "Actions".

AWS_REGION: Enter the AWS Region for your AWS resources, that you used when you set up the terraform. example `us-west-2`
AWS_GITHUB_ROLE: Enter the ARN of the GitHubActions_Push_Role which is this, replacing YOUR_ACCOUNT_ID with your integer AWS account number: `arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActions_Push_Role`

### Finish terraform resources

Push up the new changes to your repo (terraform files) to trigger the write to AWS.

Return to the `aws_terraform_bgg` directory and run `make setup_boardgamegeek`

## Running the Code Modules

### Module Order
The module orders are also set out in the Orchestration, under `aws_dagster_bgg.assets.assets.py`.

Primary chain chain; Dagster job `bgg_job`
- `modules/bgg_boardgame_file_retrieval` - Gets the `boardgames_ranks.csv` file from BGG and saves it to S3.
- `lambda_functions.generate_game_urls_lambda.py` - Generates games urls for the games scraper.
- `modules/bgg_scraper/main.py` with `scraper_type="games"` - scrape game info from the games urls.
- `modules/bgg_data_cleaner_game/main.py` - Clean the scraped games data.
- `lambda_functions.generate_ratings_urls_lambda.py` - Generate ratings urls for the ratings scraper.
- `modules/bgg_scraper/main.py` with `scraper_type="ratings"` - Scrapes ratings info from the game data.
- `modules/ratings_daga_cleaner/main.py` - Clean the scraped ratings data.

Optional chain; Dagster job `user_job`
- `lambda_functions.generate_user_urls_lambda.py` (Optional) - If you desperately want DATES on your user ratings, you must run this and the next section. This is VERY EXPENSIVE (>$30)



### 01 - Get boardgames_ranks.csv file from BGG and save it to S3
- `bgg_boardgame_file_retrieval.get_bgg_games_file.py`
- Gets the `boardgames_ranks.csv` file from BGG and saves it to S3. A BGG account is required for this.

### 02 - Generate GAME scraping URLS
- `lambda_functions.generate_game_urls_lambda.py`
- Must have `boardgames_ranks.csv` in directory `data` OR on S3 from the [prior step](#01---get-boardgames_ranks.csv-file-from-bgg-and-save-it-to-s3). Download from BGG or use [Step 01](#01---get-boardgames_ranks.csv-file-from-bgg-and-save-it-to-s3) to write it to S3.
- Opens the `boardgames_ranks.csv` file and generates urls for the game scraper. Writes URLS locally when run locally, and always writes URLs to S3.

### 03 - Scrape games from URLS

- TEST LOCAL - `bgg_scraper.main.py` for GAME to test a single file locally
    - Use to test a single specific url file. Must have generated game urls first with step 02.
    - Run locally and pass the scraper type `game` as an arg, and an existing filename without directory or suffix from `data/prod/games/scraper_urls_raw/`
    - Example: `python bgg_scraper/main.py game group1_games_scraper_urls_raw`
    - Only saves data locally to `data/prod/games/scraped_xml_raw`

- TEST ON AWS - `lambda_functions.dev_bgg_scraper_fargate_trigger` for GAME will trigger process to run and write scraping on S3    
    - Must have generated game urls first with step 02.
    - Scrapes the URLs generated by step #2. This script will always trigger tasks on AWS. The DEV function will only run a single URL from a single file, so this is safely inexpensive.
    - On AWS, navigate to lambda
    - From lambda, select `dev_bgg_scraper_fargate_trigger`
    - To manually run, go to the "Test" tab
    - In the "Event JSON" section, replace the existing keys with `"scraper_type": "games"`.  It is recommended to enter in an event name and save the json for future.
    - Click "Test" to run.

- PROD - `lambda_functions.bgg_scraper_fargate_trigger` for GAME will trigger process to run and write scraping on S3    
    - Must have generated game urls first with step 02.
    - Scrapes the URLs generated by step #2. This script will always trigger tasks on AWS. DO NOT RUN WITHOUT INTENT costs ~$2 per run.
    - On AWS, navigate to lambda
    - From lambda, select `bgg_scraper_fargate_trigger`
    - To manually run, go to the "Test" tab
    - In the "Event JSON" section, replace the existing keys with `"scraper_type": "games"`.  It is recommended to enter in an event name and save the json for future.
    - Click "Test" to run.

### 04 Clean raw scraped GAME data

- `modules.bgg_data_cleaner_game.main.py`
    - Takes the scraped files and composes into various dirty data frames of full data. Writes these locally. Will only write to S3 if run on AWS.
    - Step 03 needs to have run at least once for this to work, although two sample files from local will also suffice for testing.
    - If files are present on S3, it will download all of them for this process. If there are no files on S3 yet, it will use files in `data/prod/games/scraped_xml_raw`

### 05 Generate RATINGS scraping URLS

- `lambda_functions.generate_ratings_urls_lambda.py`
- Must have `games.pkl` in directory `data/prod/game_dfs_dirty` OR on S3 from prior step.
- Loads the `games.pkl` file generated by 04 and generates ratings ratings urls. Will attempt to load games.pkl locally, otherwise will retrieve it from S3.

### 06 Scrape ratings from URLS
Scrapes ratings info from the game data. Code-wise this calls the same API and gets the same game info as the game data scraper, but where the game data scraper will pull only the first page of a given game, this scraper will paginate through all pages of a game's ratings to get all rating data.

- PROD - `lambda_functions.bgg_scraper_fargate_trigger` for RATINGS will trigger process to run and write scraping on S3
    - Must have generated game urls first with step 5.
    - Scrapes the URLs generated by step #5. This script will always trigger tasks on AWS. DO NOT RUN WITHOUT INTENT costs ~$15 per run.
    - Must run with arg for scraper type "ratings" example `python lambda_functions.bgg_scraper_fargate_trigger.py user`

- TEST - `bgg_scraper.main.py` for RATINGS
    - Use to test a single specific url file. Must have generated ratings urls first with step 05.
    - Run locally and pass both scraper type `ratings` as an arg, and an existing filename without directory or suffix from `data/prod/ratings/scraper_urls_raw/`
    - Example: `python bgg_scraper/main.py ratings group1_ratings_scraper_urls_raw`
    - Only saves data locally to `data/prod/ratings/scraped_xml_raw`

### 07 Clean raw scraped RATINGS data

- `modules.bgg_ratings_data_cleaner.main.py`
    - Takes the scraped files and composes into various dirty data frames of full data. Writes these locally. Will only write to S3 if run on AWS.
    - Step 06 needs to have run at least once for this to work, although two sample files from local will also suffice for testing.

## OPTIONAL chains

### 08 Generate USER scraping URLS 

- `lambda_functions.generate_user_urls_lambda.py`
- Must have `games.pkl` in directory `data/prod/game_dfs_dirty` OR on S3 from prior step.
- Loads the `games.pkl` file generated by 04 and generates ratings ratings urls. Will attempt to load games.pkl locally, otherwise will retrieve it from S3.

### 09 Scrape users from URLS

- PROD - `lambda_functions.bgg_scraper_fargate_trigger` for USER will trigger process to run and write scraping on S3
    - Must have generated game urls first with step 5.
    - Scrapes the URLs generated by step #5. This script will always trigger tasks on AWS. DO NOT RUN WITHOUT INTENT costs over $30 per run.
    - Must run with arg for scraper type "ratings" example `python lambda_functions.bgg_scraper_fargate_trigger.py user`

- TEST - `modules.bgg_scraper.main.py` for USER
    - Use to test a single specific url file. Must have generated ratings urls first with step 05.
    - Run locally and pass both scraper type `users` as an arg, and an existing filename without directory or suffix from `data/prod/users/scraper_urls_raw/`
    - Example: `python bgg_scraper/main.py ratings group1_ratings_scraper_urls_raw`
    - Only saves data locally to `data/prod/ratings/scraped_xml_raw`

## I added some new stuff to my deployment. How do I update it?

`make update`

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