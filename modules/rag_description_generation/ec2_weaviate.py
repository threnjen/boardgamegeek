import os
import time

import boto3
from pydantic import BaseModel


class Ec2(BaseModel):
    instance_id: str = None
    ec2_client: boto3.client = boto3.client("ec2")
    ip_address: str = None

    def copy_docker_compose_to_instance(self):
        """Run a local command to copy the file to the instance"""

        ip_dashed = self.ip_address.replace(".", "-")
        command = f"scp -i ~/.ssh/weaviate-ec2.pem modules/rag_description_generation/docker-compose.yml ec2-user@ec2-{ip_dashed}.us-west-2.compute.amazonaws.com:/home/ec2-user"

        print(f"Copying docker_compose.yml to the instance {self.instance_id}")

        response = os.system(command)

    def start_docker(self):
        ssm_client = boto3.client("ssm")

        command = "sudo docker compose -f /home/ec2-user/docker-compose.yml up -d"

        response = ssm_client.send_command(
            InstanceIds=[self.instance_id],
            DocumentName="AWS-RunShellScript",  # For Linux instances
            Parameters={"commands": [command]},
        )
        command_id = response["Command"]["CommandId"]

        print(f"Waiting for docker containers to start")
        time.sleep(5)

        command_invocation_result = ssm_client.get_command_invocation(
            CommandId=command_id, InstanceId=self.instance_id
        )

    def get_ip_address(self):
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
