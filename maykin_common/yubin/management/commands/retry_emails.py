from django.core.management.base import BaseCommand

from maykin_common.yubin.utils import retry_messages


class Command(BaseCommand):
    help = "Place deferred messages back in the queue."

    def add_arguments(self, parser):
        parser.add_argument(
            "-m",
            "--max-retries",
            dest="max_retries",
            type=int,
            default=0,
            help="Don't reset deferred messages with more than this many retries.",
        )

    def handle(self, *args, **options):
        max_retries = options["max_retries"]

        enqueued, failed = retry_messages(max_retries)

        self.stdout.write(self.style.SUCCESS(f"Retried emails: {enqueued=}, {failed=}"))
