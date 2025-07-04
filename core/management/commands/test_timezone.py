from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime

class Command(BaseCommand):
    help = 'Test that New Zealand timezone is working correctly'

    def handle(self, *args, **options):
        self.stdout.write('Testing New Zealand timezone configuration...')
        
        # Test timezone.now() (Django's timezone-aware now)
        django_now = timezone.now()
        self.stdout.write(f'Django timezone.now(): {django_now}')
        self.stdout.write(f'Django timezone.now() timezone: {django_now.tzinfo}')
        
        # Test converting to NZ time
        nz_tz = timezone.get_default_timezone()
        nz_now = django_now.astimezone(nz_tz)
        self.stdout.write(f'Converted to NZ time: {nz_now}')
        
        # Test current timezone setting
        from django.conf import settings
        self.stdout.write(f'Django TIME_ZONE setting: {settings.TIME_ZONE}')
        self.stdout.write(f'Django USE_TZ setting: {settings.USE_TZ}')
        
        # Test naive datetime vs timezone-aware
        naive_dt = datetime.now()
        aware_dt = timezone.now()
        self.stdout.write(f'Naive datetime: {naive_dt} (tzinfo: {naive_dt.tzinfo})')
        self.stdout.write(f'Timezone-aware datetime: {aware_dt} (tzinfo: {aware_dt.tzinfo})')
        
        self.stdout.write('Timezone test completed!') 