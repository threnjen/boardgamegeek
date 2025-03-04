import boto3
import pandas as pd


def lambda_handler(event, context):
    """
    AWS Lambda function to log BGG stats to DynamoDB.
    """
    dynamodb_client = boto3.client("dynamodb")

    # get data frame from S3
