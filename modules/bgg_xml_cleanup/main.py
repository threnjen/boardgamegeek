import os
import sys
import xml.etree.ElementTree as ET

from config import CONFIGS
from utils.processing_functions import (
    get_xml_file_keys_based_on_env,
    load_file_local_first,
    save_file_local_first,
    delete_file_local_first,
)

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False").lower() == "true" else False
WORKING_DIR = (
    CONFIGS["prod_directory"] if ENVIRONMENT == "prod" else CONFIGS["dev_directory"]
)


class XMLCleanup:

    def __init__(self, scraper_type: str) -> None:
        self.scraper_type = scraper_type
        self.scraper_configs = CONFIGS[scraper_type]
        self.output_file_string = self.scraper_configs["output_raw_xml_suffix"]
        print(f"\n\nProcessing items of type {self.scraper_type}...")

    def data_extraction_chain(self):
        new_xml_files_to_process, old_combined_xml_files = (
            self._get_xml_processing_lists()
        )
        self._delete_existing_xml_files(old_combined_xml_files)
        combined_file_groups = self._create_combined_file_groups(
            new_xml_files_to_process
        )
        self._process_raw_xml_files(combined_file_groups)
        self._delete_existing_xml_files(new_xml_files_to_process)

    def _get_xml_processing_lists(self) -> tuple[list, list]:
        xml_directory_files = get_xml_file_keys_based_on_env(
            xml_directory=self.scraper_configs["output_xml_directory"]
        )
        new_xml_files_to_process = [
            x for x in xml_directory_files if x.split("/")[-1].startswith("group")
        ]
        old_combined_xml_files = [
            x for x in xml_directory_files if x.split("/")[-1].startswith("combined")
        ]
        return new_xml_files_to_process, old_combined_xml_files

    def _delete_existing_xml_files(self, existing_files: list):
        for file in existing_files:
            bucket_stripped_path = file.replace(f"s3://{S3_SCRAPER_BUCKET}/", "")
            delete_file_local_first(
                file_name=bucket_stripped_path,
            )

    def _create_combined_file_groups(
        self, new_xml_files_to_process: list
    ) -> dict[list]:
        combined_file_groups = {}
        for file in new_xml_files_to_process:
            group = file.split("/")[-1].split("_")[0]
            if group not in combined_file_groups:
                combined_file_groups[group] = []
            combined_file_groups[group].append(file)
        return combined_file_groups

    def _save_xml_files(self, combined_group_entries: list, group: str) -> None:

        save_file_local_first(
            path=self.scraper_configs["output_xml_directory"],
            file_name=self.output_file_string.replace("{}", group),
            data=combined_group_entries,
        )

    def _process_raw_xml_files(self, combined_file_groups: list) -> dict[list]:

        print("\nProcessing raw XML files")
        total_games_processed = 0

        for file_group in combined_file_groups:
            this_group_games_processed = 0
            new_xml_files_to_process = combined_file_groups[file_group]

            root = ET.Element(
                "items", termsofuse="https://boardgamegeek.com/xmlapi/termsofuse"
            )

            for file in new_xml_files_to_process:
                local_open = load_file_local_first(
                    path=self.scraper_configs["output_xml_directory"],
                    file_name=file.split("/")[-1],
                )

                root_element = ET.fromstring(local_open)

                # Append each <item> to the new root
                for item in root_element.findall("item"):
                    root.append(item)
                    this_group_games_processed += 1
                    total_games_processed += 1

            # Convert the ElementTree to a string
            xml_declaration = '<?xml version="1.0" encoding="utf-8"?>\n'
            xml_string = xml_declaration + ET.tostring(
                root, encoding="utf-8", method="xml"
            ).decode("utf-8")
            self._save_xml_files(xml_string, file_group)

            print(
                f"Processed {this_group_games_processed} items from group {file_group}\n"
            )

        print(f"\nTotal items processed: {total_games_processed}")


if __name__ == "__main__":

    scraper_type = sys.argv[1]

    XMLCleanup(scraper_type=scraper_type).data_extraction_chain()
