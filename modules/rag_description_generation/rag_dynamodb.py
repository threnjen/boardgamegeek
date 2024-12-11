import boto3
from pydantic import BaseModel


class DynamoDB(BaseModel):
    dynamodb_client: boto3.client = boto3.client("dynamodb")

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
        )
        cons = summary.split("\n\n### Cons\n")[-1].replace("\n", "").replace("-", "")

        response = self.dynamodb_client.put_item(
            TableName="game_generated_descriptions",
            Item={
                "game_id": {"S": game_id},
                "generated_description": {"S": description},
                "generated_pros": {"S": pros},
                "generated_cons": {"S": cons},
            },
            ConditionExpression="attribute_not_exists(game_id)",
        )
        print(response)

    def check_dynamo_db_key(self, game_id: str) -> bool:
        try:
            self.dynamodb_client.get_item(
                TableName="game_generated_descriptions", Key={"game_id": {"S": game_id}}
            )["Item"]
            print(f"Game {game_id} already exists in DynamoDB")
            return True
        except:
            return False
