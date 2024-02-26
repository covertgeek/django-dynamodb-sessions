from ast import Del

from botocore.exceptions import ClientError
from django.core.management import BaseCommand

from dynamodb_sessions.backends.dynamodb import TABLE_NAME, dynamodb_connection_factory


class Command(BaseCommand):
    help = "delete session table if does not exist"

    def add_arguments(self, parser):
        parser.add_argument(
            "--ignore_logs",
            "--ignore_logs",
            default=False,
            help="Boolean ",
            action="store_true",
            dest="ignore_logs",
        )
        # Add option to delete table with deletion protection
        parser.add_argument(
            "--force",
            "-f",
            default=False,
            action="store_true",
            dest="force",
            help="Remove deletion protection and delete table",
        )

    def handle(self, *args, **options):
        connection = dynamodb_connection_factory(low_level=True)
        # check table exists
        if not connection.describe_table(TableName=TABLE_NAME):
            if not options.get("ignore_logs"):
                self.stdout.write("session table does not exist\n")
            return

        try:
            if options.get("force"):
                connection.update_table(
                    TableName=TABLE_NAME, DeletionProtectionEnabled=False
                )

            connection.delete_table(TableName=TABLE_NAME)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ValidationException":
                if not options.get("ignore_logs"):
                    self.stdout.write("Deletion protection is active\n")
                    exit(-1)

        if not options.get("ignore_logs"):
            self.stdout.write("{0} dynamodb table deleted".format(TABLE_NAME))
