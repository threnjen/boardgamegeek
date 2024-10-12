import re
import os
import boto3, botocore
from typing import Union


def check_bucket(bucket_name: str) -> Union[bool, str]:
    # check if the bucket name is already taken
    s3 = boto3.resource("s3")
    try:
        s3.meta.client.head_bucket(Bucket=bucket_name)
        return True
    except botocore.exceptions.ClientError as e:
        error_code = int(e.response["Error"]["Code"])
        if error_code == 403:
            return "This bucket name is taken by another account. Please choose another name."
        elif error_code == 404:
            return True
        else:
            return "An error occurred while checking the bucket name. ARE YOUR CREDS EXPORTED?"


def validated_project_name(bucket_name: str) -> Union[bool, str]:
    if not bucket_name:
        return "Bucket name cannot be empty. Check in your .env that the TF_VAR_BUCKET is set"

    # check that project name only has letters, numbers, underscore, or dash
    if not re.match("^[a-zA-Z0-9_-]*$", bucket_name):
        return "Bucket name must only contain letters, numbers, underscore, or dash"

    # check that project name starts with a letter
    if not bucket_name[0].isalpha():
        return "Bucket name must start with a letter"

    return check_bucket(bucket_name)


def validated_region(project_region: str) -> Union[bool, str]:
    if not project_region:
        return "Region cannot be empty"

    # check that project region is in the correct format
    if not re.match("^[a-z]{2}-[a-z]+-[0-9]$", project_region):
        return "Region must be in the format of us-region-#"

    return True


def run_validations(region: str, bucket_name: str) -> str:

    if not validated_project_name(bucket_name):
        return validated_project_name(bucket_name)
    if not validated_region(region):
        return validated_region(region)

    return "validated"


if __name__ == "__main__":

    bucket_name = os.environ.get("TF_VAR_BUCKET")
    region = os.environ.get("TF_VAR_REGION")

    validation_report = run_validations(region, bucket_name)

    print(validation_report)
