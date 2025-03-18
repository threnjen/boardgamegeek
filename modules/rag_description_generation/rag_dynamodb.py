from datetime import datetime

import boto3
from pydantic import BaseModel


class RagDynamoDB(BaseModel):
    dynamodb_client: boto3.client = boto3.client("dynamodb")
    today_timestring: str = datetime.now().strftime("%Y%m%d")
    days_since_last_process: int = 30

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
        print(description)
        print(pros)
        print(cons)
        print(f"Game {game_id} processed and added to DynamoDB")

    def check_dynamo_db_key(self, game_id: str) -> bool:

        default_timestamp = "19700101"

        try:
            item = self.dynamodb_client.get_item(
                TableName="game_generated_descriptions", Key={"game_id": {"S": game_id}}
            )["Item"]
            db_timestamp_str = item.get("date_updated", {"S": default_timestamp})["S"]
            db_timestamp = datetime.strptime(db_timestamp_str, "%Y%m%d")

            # determine if datetime.now() is more than days_since_last_process days after the db_timestamp
            if (datetime.now() - db_timestamp).days < self.days_since_last_process:
                print(
                    f"Game {game_id} already processed within last {self.days_since_last_process} days"
                )
                return True
            print(
                f"Game {game_id} found but not processed within last {self.days_since_last_process} days"
            )
            return False
        except:
            print(f"Game {game_id} not found in DynamoDB")
            return False
