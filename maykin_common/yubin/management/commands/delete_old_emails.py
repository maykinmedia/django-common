from django.core.management.base import BaseCommand

from django_yubin.models import Message


class Command(BaseCommand):
    help = "Delete old emails from the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Delete emails older than specified days (default: 90)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        (deleted, _), cutoff_date = Message.delete_old(days)

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted old emails: {deleted=}, cutoff_date={cutoff_date.date()}"
            )
        )
