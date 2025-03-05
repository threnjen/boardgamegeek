from datetime import datetime

import boto3
from pydantic import BaseModel


class DynamoDB(BaseModel):
    dynamodb_client: boto3.client = boto3.client("dynamodb")
    today_timestring: str = datetime.now().strftime("%Y%m%d")

    def divide_and_process_generated_summary(self, game_id: str, summary: str) -> None:
        summary = summary.replace("**", "")
        description = summary.split("\n\n### Pros\n")[0].replace(
            "### What is this game about?\n", ""
        )
        pros = (
            summary.split("\n\n### Pros\n")[1]
            .split("\n\n### Cons\n")[0]
            .replace("\n", "")
            .replace("-", "")
            .strip()
        )
        cons = (
            summary.split("\n\n### Cons\n")[-1]
            .replace("\n", "")
            .replace("-", "")
            .strip()
        )

        response = self.dynamodb_client.put_item(
            TableName="game_generated_descriptions",
            Item={
                "game_id": {"S": game_id},
                "generated_description": {"S": description},
                "generated_pros": {"S": pros},
                "generated_cons": {"S": cons},
                "date_updated": {"S": self.today_timestring},
            },
            # ConditionExpression="attribute_not_exists(game_id)",
        )
        print(f"Game {game_id} processed and added to DynamoDB")

    def check_dynamo_db_key(self, game_id: str) -> bool:

        # make a default timestamp that is the standard 1970 01 01 default
        default_timestamp = "19700101"
        days_since_last_process = 30

        try:
            item = self.dynamodb_client.get_item(
                TableName="game_generated_descriptions", Key={"game_id": {"S": game_id}}
            )["Item"]
            db_timestamp_str = item.get("date_updated", {"S": default_timestamp})["S"]
            db_timestamp = datetime.strptime(db_timestamp_str, "%Y%m%d")

            # determine if datetime.now() is more than three days after the db_timestamp
            if (datetime.now() - db_timestamp).days < days_since_last_process:
                print(
                    f"Game {game_id} already processed within last {days_since_last_process} days"
                )
                return True
            print(
                f"Game {game_id} found but not processed within last {days_since_last_process} days"
            )
            return False
        except:
            print(f"Game {game_id} not found in DynamoDB")
            return False
