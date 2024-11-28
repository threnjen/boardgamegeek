import os
import xml.etree.ElementTree as ET

from config import CONFIGS
from utils.s3_file_handler import S3FileHandler
from utils.local_file_handler import LocalFileHandler
from utils.processing_functions import (
    get_local_keys_based_on_env,
    load_file_local_first,
    save_file_local_first,
)

S3_SCRAPER_BUCKET = os.environ.get("S3_SCRAPER_BUCKET")
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False").lower() == "true" else False
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
WORKING_DIR = (
    CONFIGS["dev_directory"] if ENVIRONMENT == "dev" else CONFIGS["prod_directory"]
)


class XMLParser:

    def __init__(self, scraper_type: str, urls_filename: str) -> None:
        self.file_group = urls_filename.split("_")[0]
        self.urls_filename = urls_filename.split(".")[0]
        self.bot_scraper_name = CONFIGS[scraper_type]["scrapy_bot_name"]
        self.raw_urls_folder = CONFIGS[scraper_type]["raw_urls_directory"]
        self.scraped_files_folder = CONFIGS[scraper_type]["output_xml_directory"]
        self.scraper_type = scraper_type
        self.s3_file_handler = S3FileHandler()
        self.local_file_handler = LocalFileHandler()

    def parser_process_chain(self):

        raw_xml = self._combine_xml_files_to_master()

        file_name = CONFIGS[self.scraper_type]["output_raw_xml_suffix"].replace(
            "{}", self.file_group
        )

        save_file_local_first(
            path=self.scraped_files_folder,
            file_name=file_name,
            data=raw_xml,
        )

    def download_xml(self, file_path: str):
        if IS_LOCAL:
            return load_file_local_first(path=self.save_file_path, file_name=file_path)
        else:
            file = self.s3_file_handler.load_xml(f"{WORKING_DIR}{file_path}")
            self.local_file_handler.save_xml(
                file_path=f"{WORKING_DIR}{self.save_file_path}/{file_path}", data=file
            )

    def _combine_xml_files_to_master(self) -> str:
        """Combine the XML files into a single XML file"""

        print(f"\n\nCombining XML files for {self.file_group}")

        print(get_local_keys_based_on_env(self.scraped_files_folder))

        saved_files = [
            x
            for x in get_local_keys_based_on_env(self.scraped_files_folder)
            if "combined" not in x and ".gitkeep" not in x
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

            if self.scraper_type == "users":
                user_name = xml_file.split("user_")[-1].split(".xml")[0]
                user_tag = ET.SubElement(combined_root, "username", value=user_name)

                # Append each <item> element to the new root
                for item in root.findall("item"):
                    user_tag.append(item)
            else:
                # Append each <item> element to the new root
                for item in root.findall("item"):
                    combined_root.append(item)

        # Create a new XML tree and write it to a new file
        combined_tree = ET.ElementTree(combined_root)

        # Get the root element from the ElementTree
        combined_root = combined_tree.getroot()

        xml_bytes = ET.tostring(combined_root, encoding="utf-8", xml_declaration=True)

        if IS_LOCAL and ENVIRONMENT == "dev":
            # remove the saved files
            for xml_file in saved_files:
                os.remove(xml_file)

        return xml_bytes
