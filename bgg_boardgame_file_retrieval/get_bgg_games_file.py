import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from tempfile import mkdtemp
import awswrangler as wr

BGG_USERNAME = os.environ.get("BGG_USERNAME")
BGG_PASSWORD = os.environ.get("BGG_PASSWORD")
ENV = os.environ.get("ENV", "dev")
S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")

# Get this file manually from https://boardgamegeek.com/data_dumps/bg_ranks
def initialize_driver():

    if not os.environ.get("ENV", "dev") == "prod":
        return webdriver.Chrome()
    
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
    chrome_options.binary_location = "/opt/chrome/chrome-linux64/chrome"

    service = Service(
        executable_path="/opt/chrome-driver/chromedriver-linux64/chromedriver",
        service_log_path="/tmp/chromedriver.log"
    )

    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )

    return driver

def lambda_handler(event, context):
    driver = initialize_driver()

    driver.get('https://boardgamegeek.com/login')

    title = driver.title
    print(title)

    driver.find_element(by='id',value="inputUsername").send_keys(BGG_USERNAME)
    driver.find_element(by='id',value="inputPassword").send_keys(BGG_PASSWORD)

    driver.find_element(by='css selector',value="button[type='submit']").click()

    time.sleep(3)

    driver.get("https://boardgamegeek.com/data_dumps/bg_ranks")

    download_element = driver.find_element(By.LINK_TEXT, 'Click to Download').get_attribute('href')

    print(f'The main content is: {download_element}')

    local_file_path = "." if ENV == "dev" else "/tmp"
    with open(f"{local_file_path}/boardgames_ranks.csv", "w") as f:
        f.write(download_element)

    wr.s3.upload(local_file=f"{local_file_path}/boardgames_ranks.csv", path=f's3://{S3_SCRAPER_BUCKET}/boardgames_ranks.csv')

if __name__=="__main__":
    lambda_handler(None, None)