import argparse
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from functools import partial

import scrapy
from scraper_config import SCRAPER_CONFIG
from scrapy.crawler import CrawlerProcess
from scrapy_settings import *

from config import DIRECTORY_CONFIGS
from utils.load_save import DataSaver, LocalLoader, LocalSaver, S3Loader, S3Saver
from utils.read_write import JSONReader, JSONWriter, XMLWriter

S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
ENV = os.environ.get("ENV", "dev")


class BGGSpider(scrapy.Spider):
    """Spider to scrape BGG for game data"""

    def __init__(
        self,
        name: str,
        scraper_urls_raw: list[str],
        filename: str,
        saver: DataSaver,
    ):
        """
        Parameters:
        name: str
            The name of the spider
        save_folder: str
            The folder to save the data to
        scraper_urls_raw: list[str]
            The urls to scrape
        """
        self.name = name
        super().__init__()
        self.scraper_urls_raw = scraper_urls_raw
        self.filename = filename
        self.saver = saver

    def start_requests(self):
        for i, url in enumerate(self.scraper_urls_raw):
            print(f"Starting URL {i}: {url}")
            save_response_with_index = partial(self._save_response, response_id=i)
            yield scrapy.Request(url=url, callback=save_response_with_index)

    def _save_response(self, response: scrapy.http.Response, response_id: int):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.saver.save_data(
            response.body, f"{self.filename}{response_id}_{timestamp}.xml"
        )


class GameScraper:

    def __init__(self, scraper_type, filename) -> None:
        self.file_group = filename.split("_")[0]
        self.filename = filename
        self.scraped_games_save = SCRAPER_CONFIG[scraper_type]["save_subfolder"]
        self.scraper_type = scraper_type

    def run_game_scraper_processes(self):
        scraper_urls_raw = self._load_scraper_urls()
        self._run_scrapy_scraper(scraper_urls_raw)
        raw_xml = self._combine_xml_files_to_master()
        self._write_master_xml_file(
            raw_xml, xml_filename=f"master_{self.file_group}_{self.scraper_type}_raw.xml"
        )

    def _load_scraper_urls(self) -> list[str]:
        # get file from local if dev, else from S3

        local_path = SCRAPER_CONFIG[self.scraper_type]["local_path"]
        if os.path.exists(f"{local_path}/{self.filename}.json"):
            scraper_urls_raw = LocalLoader(JSONReader(), local_path).load_data(
                f"{self.filename}.json"
            )
        else:
            scraper_urls_raw = S3Loader(
                JSONReader(),
                f"{SCRAPER_CONFIG[scraper_type]["s3_location"]}",
            ).load_data(f"{self.filename}.json")

        if ENV == "dev":
            if not os.path.exists(f"{local_path}/{self.filename}.json"):
                LocalSaver(
                    JSONWriter(),
                    local_path
                ).save_data(data=scraper_urls_raw, filename=f"{self.filename}.json")
            scraper_urls_raw = scraper_urls_raw[:10]
            print(scraper_urls_raw)

        return scraper_urls_raw

    def _run_scrapy_scraper(self, scraper_urls_raw) -> None:
        process = CrawlerProcess(
            settings={
                "LOG_LEVEL": "DEBUG",
                "BOT_NAME": SCRAPER_CONFIG[scraper_type]["bot_name"],
                "ROBOTSTXT_OBEY": ROBOTSTXT_OBEY,
                "DOWNLOAD_DELAY": DOWNLOAD_DELAY,
                "COOKIES_ENABLED": COOKIES_ENABLED,
                "AUTOTHROTTLE_ENABLED": AUTOTHROTTLE_ENABLED,
                "AUTOTHROTTLE_START_DELAY": AUTOTHROTTLE_START_DELAY,
                "AUTOTHROTTLE_MAX_DELAY": AUTOTHROTTLE_MAX_DELAY,
                "AUTOTHROTTLE_TARGET_CONCURRENCY": AUTOTHROTTLE_TARGET_CONCURRENCY,
                "AUTOTHROTTLE_DEBUG": AUTOTHROTTLE_DEBUG,
            }
        )

        process.crawl(
            BGGSpider,
            name="bgg_raw",
            scraper_urls_raw=scraper_urls_raw,
            filename=self.filename,
            saver=LocalSaver(XMLWriter(), self.scraped_games_save),
        )

        process.start()

        # Testing section to see what happens after we are done with process.start()
        print("Completed with scraping process")

    def _combine_xml_files_to_master(self) -> str:
        """Combine the XML files into a single XML file"""

        print(f"Combining XML files for {self.file_group}")

        saved_files = [
            f"{self.scraped_games_save}/{x}"
            for x in os.listdir(self.scraped_games_save)
            if self.file_group in x
        ]

        # Parse the first XML file to get the root and header
        tree = ET.parse(saved_files[0])
        root = tree.getroot()

        # Create a new root element for the combined XML
        combined_root = ET.Element(root.tag, root.attrib)

        # Iterate over each XML file
        for xml_file in saved_files:
            # Parse the XML file
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Append each <item> element to the new root
            for item in root.findall("item"):
                combined_root.append(item)

        # Create a new XML tree and write it to a new file
        combined_tree = ET.ElementTree(combined_root)

        # Get the root element from the ElementTree
        combined_root = combined_tree.getroot()

        xml_bytes = ET.tostring(combined_root, encoding="utf-8", xml_declaration=True)

        if ENV == "dev":
            # remove the saved files
            for xml_file in saved_files:
                os.remove(xml_file)

        return xml_bytes

    def _write_master_xml_file(self, xml_bytes: bytes, xml_filename=str) -> None:

        LocalSaver(XMLWriter(), self.scraped_games_save).save_data(xml_bytes, xml_filename)

        if ENV == "prod":
            S3Saver(XMLWriter(), self.scraped_games_save).save_data(xml_bytes, xml_filename)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "scraper_type",
        type=str,
        help="The type of scraper to run.  Current options are 'game' and 'user'",
    )
    parser.add_argument(
        "filename",
        type=str,
        help=f"The filename to process from path local_files/{DIRECTORY_CONFIGS['scraper_urls_raw_game']}, without a suffix",
    )
    return parser.parse_args()


if __name__ == "__main__":

    args = parse_args()
    scraper_type = args.scraper_type
    filename = args.filename

    GameScraper(scraper_type, filename).run_game_scraper_processes()
