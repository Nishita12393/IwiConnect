from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from core.models import PasswordResetToken


class Command(BaseCommand):
    help = 'Clean up expired and used password reset tokens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        # Find expired and used tokens
        expired_tokens = PasswordResetToken.objects.filter(
            models.Q(is_used=True) | models.Q(expires_at__lt=timezone.now())
        )
        
        count = expired_tokens.count()
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(
                    f'Would delete {count} expired/used password reset tokens'
                )
            )
            for token in expired_tokens[:10]:  # Show first 10 as examples
                self.stdout.write(f'  - {token.user.email} (expires: {token.expires_at})')
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        else:
            expired_tokens.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {count} expired/used password reset tokens'
                )
            ) 