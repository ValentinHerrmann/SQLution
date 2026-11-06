from django.core.management.base import BaseCommand

from myapp.utils.account_management import apply_schedules


class Command(BaseCommand):
    help = 'Lock and delete accounts whose scheduled lock/deletion time has passed.'

    def handle(self, *args, **options):
        result = apply_schedules()
        self.stdout.write(self.style.SUCCESS(
            f"Locked {result['locked']} account(s), deleted {result['deleted']} account(s), "
            f"released {result['released_prefixes']} prefix(es)."
        ))
