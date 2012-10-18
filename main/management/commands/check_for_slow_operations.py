from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from wardenclyffe.main.models import Operation
from wardenclyffe.util.mail import send_slow_operations_email


class Command(BaseCommand):
    args = ''
    help = ''

    def handle(self, *args, **kwargs):
        status_filters = ["enqueued", "in progress", "submitted"]
        operations = Operation.objects.filter(
            status__in=status_filters,
            modified__lt=datetime.now() - timedelta(hours=1)
            ).order_by("-modified")
        if operations.count() > 0:
            send_slow_operations_email(operations)
        # else, no slow operations to warn about. excellent.
