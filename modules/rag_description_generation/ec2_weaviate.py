import boto3
import time
from pydantic import BaseModel


class Ec2(BaseModel):
    instance_id: str = None
    ec2_client: boto3.client = boto3.client("ec2")
    ip_address: str = None

    def start_docker(self):
        ssm_client = boto3.client("ssm")

        command = "docker compose up -d"

        print(f"\nSending the command: {command} to the instance {self.instance_id}")

        response = ssm_client.send_command(
            InstanceIds=[self.instance_id],
            DocumentName="AWS-RunShellScript",  # For Linux instances
            Parameters={"commands": [command]},
        )
        print(response)

    def get_ip_address(self):
        print(self.ip_address)
        return self.ip_address

    def validate_ready_weaviate_instance(self):

        self.instance_id = self.get_correct_instance_id()

        self.verify_running_instance()

        self.ip_address = self.describe_instance()["Instances"][0]["PublicIpAddress"]

    def get_correct_instance_id(self):
        """Get the instance id of the weaviate_embedder instance"""
        instances = self.ec2_client.describe_instances()["Reservations"]

        for instance in instances:

            instance_tags = instance["Instances"][0]["Tags"]

            for tag in instance_tags:
                if tag["Key"] == "Name":
                    if tag["Value"] == "weaviate_embedder":
                        return instance["Instances"][0]["InstanceId"]

    def verify_running_instance(self):

        response = self.describe_instance()

        running_code = response["Instances"][0]["State"]["Code"]

        if running_code == 16:
            pass

        else:
            print(f"Starting the instance {self.instance_id}")
            self.ec2_client.start_instances(
                InstanceIds=[
                    self.instance_id,
                ]
            )

            while running_code != 16:
                time.sleep(60)
                response = self.describe_instance()
                running_code = response["Instances"][0]["State"]["Code"]

            self.start_docker()

        print(f"Instance {self.instance_id} is running")
        return True

    def stop_instance(self):
        print(f"Stopping the instance {self.instance_id}")
        self.ec2_client.stop_instances(
            InstanceIds=[
                self.instance_id,
            ]
        )

    def describe_instance(self):
        """Get the IP address of the instance"""
        return self.ec2_client.describe_instances(
            InstanceIds=[
                self.instance_id,
            ]
        )[
            "Reservations"
        ][0]
