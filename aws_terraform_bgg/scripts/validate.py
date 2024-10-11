import re
import os
import boto3, botocore


def check_bucket(bucket_name):
    # check if the bucket name is already taken
    s3 = boto3.resource("s3")
    try:
        s3.meta.client.head_bucket(Bucket=bucket_name)
        return True
    except botocore.exceptions.ClientError as e:
        error_code = int(e.response["Error"]["Code"])
        if error_code == 403:
            print(
                "This bucket name is taken by another account. Please choose another name."
            )
            return False
        elif error_code == 404:
            return True


def validated_project_name(bucket_name):
    if not bucket_name:
        print(
            "Bucket name cannot be empty. Check in your .env that the TF_VAR_BUCKET is set"
        )
        return False

    # check that project name only has letters, numbers, underscore, or dash
    if not re.match("^[a-zA-Z0-9_-]*$", bucket_name):
        print("Bucket name must only contain letters, numbers, underscore, or dash")
        return False

    # check that project name starts with a letter
    if not bucket_name[0].isalpha():
        print("Bucket name must start with a letter")
        return False

    return check_bucket(bucket_name)


def validated_region(project_region):
    if not project_region:
        print("Region cannot be empty")
        return False

    # check that project region is in the correct format
    if not re.match("^[a-z]{2}-[a-z]+-[0-9]$", project_region):
        print("Region must be in the format of us-region-#")
        return False

    return True


def run_validations(region, bucket_name):

    if not validated_project_name(bucket_name):
        print("Bucket name failure; see specific requirements above\n")
        return "failure"
    if not validated_region(region):
        print(
            "\n\n!!!Region name failure; check in your .env that the TF_VAR_REGION is in the format of us-region-#\n"
        )
        return "failure"

    return "validated"


if __name__ == "__main__":

    bucket_name = os.environ.get("TF_VAR_BUCKET")
    region = os.environ.get("TF_VAR_REGION")

    validation_report = run_validations(region, bucket_name)

    print(validation_report)
