"""
Django command to wait for the database to be available.
"""

import time
import os
from psycopg2 import OperationalError as Psycopg2OpError
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to wait for database."""

    def handle(self, *args, **options):
        """Entrypoint for command."""
        self.stdout.write("Waiting for database...")
        db_up = False
        db_name = os.environ.get("DB_NAME")
        db_user = os.environ.get("DB_USER")
        db_host = os.environ.get("DB_HOST", "localhost")
        db_port = os.environ.get("DB_PORT", "5432")
        self.stdout.write(
            f"Trying to connect to DB {db_name} on {db_host}:{db_port} as {db_user}"
        )

        while db_up is False:
            try:
                self.check(databases=["default"])
                db_up = True
            except (Psycopg2OpError, OperationalError) as e:
                self.stdout.write(
                    f"Database unavailable, waiting 1 second... Error: {e}"
                )
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database available!"))
