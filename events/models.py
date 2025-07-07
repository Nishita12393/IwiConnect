from django.db import models
from django.conf import settings

# Create your models here.

class Event(models.Model):
    VISIBILITY_CHOICES = [
        ('PUBLIC', 'Public'),
        ('IWI', 'Iwi-specific'),
        ('HAPU', 'Hapu-specific'),
    ]
    LOCATION_TYPE_CHOICES = [
        ('PHYSICAL', 'Physical Location'),
        ('ONLINE', 'Online Event'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location_type = models.CharField(max_length=10, choices=LOCATION_TYPE_CHOICES, default='PHYSICAL')
    location = models.CharField(max_length=255, blank=True, help_text='Physical address or venue name')
    online_url = models.URLField(max_length=500, blank=True, help_text='URL for online event (required for online events)')
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='PUBLIC')
    iwi = models.ForeignKey('core.Iwi', null=True, blank=True, on_delete=models.SET_NULL, help_text='Specific iwi for iwi-specific events')
    hapu = models.ForeignKey('core.Hapu', null=True, blank=True, on_delete=models.SET_NULL, help_text='Specific hapu for hapu-specific events')
    attachment = models.FileField(upload_to='event_attachments/', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class EventParticipant(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['event', 'user']
