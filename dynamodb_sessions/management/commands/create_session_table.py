import time
from venv import logger

from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management import BaseCommand, CommandError, call_command

from dynamodb_sessions.backends.dynamodb import (
    READ_CAPACITY_UNITS,
    TABLE_NAME,
    WRITE_CAPACITY_UNITS,
    dynamodb_connection_factory,
)


class Command(BaseCommand):
    help = "creates session table if does not exist"

    def add_arguments(self, parser):
        parser.add_argument(
            "--ignore_logs",
            default=False,
            help="Boolean ",
            action="store_true",
            dest="ignore_logs",
        )
        parser.add_argument(
            "--no_protection",
            "-np",
            default=True,
            action="store_true",
            dest="no_protection",
            help="Do not use deletion protection",
        )
        parser.add_argument(
            "--no-pay-per-request",
            "-nppr",
            default=False,
            action="store_true",
            dest="no_pay_per_request",
        )
        parser.add_argument(
            "--ttl_field",
            "-ttl",
            default="ttl",
            action="store",
            dest="ttl_field",
            help="TTL field name",
        )

    def handle(self, *args, **options):
        connection = dynamodb_connection_factory(low_level=True)
        # check session table exists
        try:
            connection.describe_table(TableName=TABLE_NAME)
            if not options.get("ignore_logs"):
                self.stdout.write("session table already exist\n")
            return
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pass
            else:
                raise e

        table_args = dict(
            TableName=TABLE_NAME,
            AttributeDefinitions=[
                {"AttributeName": "session_key", "AttributeType": "S"}
            ],
            KeySchema=[{"AttributeName": "session_key", "KeyType": "HASH"}],
            BillingMode="PAY_PER_REQUEST",  # On-demand capacity
            DeletionProtectionEnabled=not options.get("no_protection"),
        )

        if options.get("no_pay_per_request"):
            table_args["BillingMode"] = "PROVISIONED"
            table_args["ProvisionedThroughput"] = {
                "ReadCapacityUnits": READ_CAPACITY_UNITS,
                "WriteCapacityUnits": WRITE_CAPACITY_UNITS,
            }

        if not settings.USE_LOCAL_DYNAMODB_SERVER:
            # Enable TTL on the specified attribute
            connection.update_time_to_live(
                TableName=TABLE_NAME,
                TimeToLiveSpecification={
                    "Enabled": True,
                    "AttributeName": settings.DYNAMODB_TTL_ATTR,
                },
            )

        connection.create_table(**table_args)
        connection.get_waiter("table_exists").wait(TableName=TABLE_NAME)
        logger.info(f"Table {TABLE_NAME} created successfully.")
