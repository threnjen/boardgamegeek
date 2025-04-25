import csv
import os
import time
import zipfile
from os.path import expanduser
from tempfile import mkdtemp

import awswrangler as wr
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from config import CONFIGS

BGG_USERNAME = os.environ.get("BGG_USERNAME")
BGG_PASSWORD = os.environ.get("BGG_PASSWORD")
ENVIRONMENT = os.environ.get("TF_VAR_RESOURCE_ENV" "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False").lower() == "true" else False


# Get this file manually from https://boardgamegeek.com/data_dumps/bg_ranks
def initialize_driver(default_directory: str) -> webdriver.Chrome:
    """Initialize the Chrome driver
    This function will initialize the Chrome driver with the necessary
    options for the scraper to work. The function will return the
    initialized driver."""

    # if not ENVIRONMENT == "prod":
    #     return webdriver.Chrome()

    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-tools")
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument(f"--user-data-dir={mkdtemp()}")
    chrome_options.add_argument(f"--data-path={mkdtemp()}")
    chrome_options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    chrome_options.add_argument("--remote-debugging-pipe")
    chrome_options.add_argument("--verbose")
    chrome_options.add_argument("--log-path=/tmp")
    prefs = {
        "download.default_directory": default_directory,
        "download_restrictions": 0,
        "download.prompt_for_download": False,  # To auto download the file
        "directory_upgrade": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.binary_location = "/opt/chrome/chrome-linux64/chrome"

    service = Service(
        executable_path="/opt/chrome-driver/chromedriver-linux64/chromedriver",
        service_log_path="/tmp/chromedriver.log",
    )

    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver


def lambda_handler(event: dict = None, context: dict = None) -> None:
    """Uses Selenium to download the BGG game ranks file
    This function will use Selenium to download the BGG game ranks file
    and upload it to S3. The function will return None."""

    default_directory = "/tmp" if not IS_LOCAL else expanduser("~")

    # if directory default_directory/Downloads does not exist, create it
    if not os.path.exists(f"{default_directory}/Downloads"):
        os.makedirs(f"{default_directory}/Downloads")

    driver = initialize_driver(default_directory)

    driver.get("https://boardgamegeek.com/login")

    title = driver.title
    print(title)

    driver.find_element(by="id", value="inputUsername").send_keys(BGG_USERNAME)
    driver.find_element(by="id", value="inputPassword").send_keys(BGG_PASSWORD)

    driver.find_element(by="css selector", value="button[type='submit']").click()

    time.sleep(5)

    driver.get("https://boardgamegeek.com/data_dumps/bg_ranks")

    download_element = driver.find_element(
        By.LINK_TEXT, "Click to Download"
    )  # .get_attribute("href")
    filename = (
        download_element.get_attribute("href")
        .split("?X-Amz-Content-Sha256")[0]
        .split("/")[-1]
    )
    download_element.click()

    time.sleep(10)

    driver.close()

    extract_directory = default_directory if not IS_LOCAL else f"data"

    with zipfile.ZipFile(f"{default_directory}/Downloads/{filename}", "r") as zip_ref:
        zip_ref.extractall(extract_directory)

    local_file = f"{extract_directory}/{CONFIGS['boardgamegeek_csv_filename']}"
    output_file = f"{extract_directory}/boardgames_ranks.tsv"

    # Input and output file paths
    input_file = local_file
    output_file = output_file

    # Convert CSV to TSV
    with open(input_file, "r") as csv_file, open(
        output_file, "w", newline=""
    ) as tsv_file:
        csv_reader = csv.reader(csv_file)
        tsv_writer = csv.writer(tsv_file, delimiter="\t")

        for row in csv_reader:
            tsv_writer.writerow(row)

    print(f"Converted {input_file} to {output_file}")

    wr.s3.upload(
        local_file=output_file,
        path=f"s3://{S3_SCRAPER_BUCKET}/data/prod/{CONFIGS['boardgamegeek_csv_filename']}",
    )

    wr.s3.upload(
        local_file=output_file,
        path=f"s3://{S3_SCRAPER_BUCKET}/data/test/{CONFIGS['boardgamegeek_csv_filename']}",
    )


if __name__ == "__main__":

    lambda_handler({}, {})
