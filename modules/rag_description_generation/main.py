from modules.rag_description_generation.ec2_weaviate import Ec2
import sys
from pydantic import BaseModel
from modules.rag_description_generation.rag_functions import (
    connect_weaviate_client_ec2,
)
from config import CONFIGS
import os
import weaviate

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
S3_SCRAPER_BUCKET = CONFIGS["s3_scraper_bucket"]
GAME_CONFIGS = CONFIGS["games"]
IS_LOCAL = True if os.environ.get("IS_LOCAL", "False").lower() == "true" else False


class RagDescription(BaseModel):
    start_block: str
    end_block: str
    ip_address: str = None
    # client: weaviate.client = None

    def model_post_init(self, __context):
        ec2_instance = Ec2()
        ec2_instance.validate_ready_weaviate_instance()
        self.ip_address = ec2_instance.get_ip_address()
        # ec2_instance.stop_instance()
        # ec2_instance.start_docker()
        self.client = connect_weaviate_client_ec2(self.ip_address)


if __name__ == "__main__":

    start_block = sys.argv[1]
    end_block = sys.argv[2]

    print(start_block, end_block)

    rag_description = RagDescription(start_block=start_block, end_block=end_block)
