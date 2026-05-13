import logging

from django.core.management.base import BaseCommand

from maykin_common.yubin.engine import send_all

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help: str = "Sends queued messages with given priority"

    def handle(self, *args, **options):

        send_all()
