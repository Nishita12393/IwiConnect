from django.db import models
from django.conf import settings

# Create your models here.

class Notice(models.Model):
    AUDIENCE_CHOICES = [
        ('ALL', 'All Users'),
        ('IWI', 'Specific Iwi'),
        ('HAPU', 'Specific Hapu'),
        # Add more as needed
    ]
    title = models.CharField(max_length=255)
    content = models.TextField()  # Use a rich text widget in forms
    attachment = models.FileField(upload_to='notice_attachments/', blank=True, null=True)
    expiry_date = models.DateTimeField()
    audience = models.CharField(max_length=10, choices=AUDIENCE_CHOICES, default='ALL')
    iwi = models.ForeignKey('core.Iwi', null=True, blank=True, on_delete=models.SET_NULL)
    hapu = models.ForeignKey('core.Hapu', null=True, blank=True, on_delete=models.SET_NULL)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    priority = models.IntegerField(default=0)

    def is_active(self):
        from django.utils import timezone
        return self.expiry_date > timezone.now()

    def __str__(self):
        return self.title

class NoticeAcknowledgment(models.Model):
    notice = models.ForeignKey(Notice, related_name='acknowledgments', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    acknowledged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('notice', 'user')
