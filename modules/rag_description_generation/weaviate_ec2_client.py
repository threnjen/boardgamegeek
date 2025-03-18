import os
import time

import boto3
from pydantic import BaseModel

IS_LOCAL = True if os.environ.get("IS_LOCAL", False).lower() == "true" else False


class WeaviateEc2(BaseModel):
    instance_id: str = None
    ec2_client: boto3.client = boto3.client("ec2")
    ip_address: str = None

    def validate_ready_weaviate_instance(self):

        self.set_instance_id()

        self.verify_running_instance()

        self.ip_address = (
            self.describe_instance()["Instances"][0]["PublicIpAddress"]
            if IS_LOCAL
            else self.describe_instance()["Instances"][0]["PrivateIpAddress"]
        )

        print(f"\nWeaviate instance running on EC2 at {self.get_ip_address()}")

    def set_instance_id(self):
        """Get the instance id of the weaviate_embedder instance"""
        instances = self.ec2_client.describe_instances()["Reservations"]

        for instance in instances:

            instance_tags = instance["Instances"][0]["Tags"]

            for tag in instance_tags:
                if tag["Key"] == "Name":
                    if tag["Value"] == "weaviate_embedder":
                        self.instance_id = instance["Instances"][0]["InstanceId"]

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

        print(f"Instance {self.instance_id} is running")
        return True

    def copy_docker_compose_to_instance(self):
        """Run a local command to copy the file to the instance"""

        ip_dashed = self.get_ip_address().replace(".", "-")
        command = f"scp -i ~/.ssh/weaviate-ec2.pem modules/rag_description_generation/docker-compose.yml ec2-user@ec2-{ip_dashed}.us-west-2.compute.amazonaws.com:/home/ec2-user"

        print(f"\nCopying docker_compose.yml to the instance {self.instance_id}")

        os.system(command)

    def check_if_weaviate_is_already_running(self):
        print("\nChecking if Weaviate is already running")
        ssm_client = boto3.client("ssm")

        command = "sudo docker container ls"
        response = ssm_client.send_command(
            InstanceIds=[self.instance_id],
            DocumentName="AWS-RunShellScript",  # For Linux instances
            Parameters={"commands": [command]},
        )
        command_id = response["Command"]["CommandId"]
        time.sleep(30)
        command_invocation_result = ssm_client.get_command_invocation(
            CommandId=command_id, InstanceId=self.instance_id
        )

        std_output_to_parse = command_invocation_result["StandardOutputContent"]
        if ("cr.weaviate.io/semitechnologies/weaviate" in std_output_to_parse) and (
            "cr.weaviate.io/semitechnologies/transformers-inference:sentence-transformers-all-mpnet-base-v2"
            in std_output_to_parse
        ):
            print("Weaviate is already running")
            return True
        else:
            print("Weaviate is not running")
            return False

    def start_weaviate_docker_containers(self):

        if self.check_if_weaviate_is_already_running():
            return

        print("\nStarting Weaviate Docker containers")

        ssm_client = boto3.client("ssm")

        self.copy_docker_compose_to_instance()

        command = "sudo docker compose -f /home/ec2-user/docker-compose.yml up -d"

        response = ssm_client.send_command(
            InstanceIds=[self.instance_id],
            DocumentName="AWS-RunShellScript",  # For Linux instances
            Parameters={"commands": [command]},
        )
        command_id = response["Command"]["CommandId"]

        print(f"Waiting for docker containers to start")

        status = "InProgress"
        while status == "InProgress":
            time.sleep(30)
            command_invocation_result = ssm_client.get_command_invocation(
                CommandId=command_id, InstanceId=self.instance_id
            )
            status = command_invocation_result["Status"]
            print(command_invocation_result["Status"])

    def get_ip_address(self):
        return self.ip_address

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
