import boto3
import time


def get_instance_id():
    """Get the IP address of the instance"""
    ec2 = boto3.client("ec2")
    instances = ec2.describe_instances()["Reservations"]
    for instance in instances:

        instance_tags = instance["Instances"][0]["Tags"]

        for tag in instance_tags:
            if tag["Key"] == "Name":
                if tag["Value"] == "weaviate_embedder":
                    return instance["Instances"][0]["InstanceId"]


def get_instance_details(instance_id):
    """Get the IP address of the instance"""
    ec2 = boto3.client("ec2")
    response = ec2.describe_instances(
        InstanceIds=[
            instance_id,
        ]
    )[
        "Reservations"
    ][0]

    running_code = response["Instances"][0]["State"]["Code"]
    if running_code != 16:
        print("Starting the instance")
        ec2.start_instances(
            InstanceIds=[
                instance_id,
            ]
        )

    while running_code != 16:
        time.sleep(60)
        response = ec2.describe_instances(
            InstanceIds=[
                instance_id,
            ]
        )[
            "Reservations"
        ][0]
        running_code = response["Instances"][0]["State"]["Code"]

    ip_address = response["Instances"][0]["PublicIpAddress"]

    return ip_address, running_code


if __name__ == "__main__":
    instance_id = get_instance_id()
    print(instance_id)
    ip_address, running_code = get_instance_details(instance_id)
