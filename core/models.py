from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import os
import uuid
from django.conf import settings
from django.utils import timezone

# Create your models here.

class Iwi(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Hapu(models.Model):
    iwi = models.ForeignKey(Iwi, related_name='hapu', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.iwi.name})"

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

def citizenship_document_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1]
    random_name = uuid.uuid4().hex + uuid.uuid4().hex[:16]
    # Store in a protected subfolder inside MEDIA_ROOT
    return f'protected_citizenship_docs/{random_name}{ext}'

class CustomUser(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    iwi = models.ForeignKey(Iwi, on_delete=models.SET_NULL, null=True, blank=True)
    hapu = models.ForeignKey(Hapu, on_delete=models.SET_NULL, null=True, blank=True)
    citizenship_document = models.FileField(upload_to=citizenship_document_upload_to, blank=True, null=True)  # type: ignore
    is_active = models.BooleanField(default=True) # type: ignore
    is_staff = models.BooleanField(default=False) # type: ignore
    registered_at = models.DateTimeField(auto_now_add=True)
    STATE_CHOICES = [
        ('PENDING_VERIFICATION', 'Pending Verification'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    ]
    state = models.CharField(max_length=32, choices=STATE_CHOICES, default='PENDING_VERIFICATION')

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.email

class IwiLeader(models.Model):
    iwi = models.ForeignKey(Iwi, on_delete=models.CASCADE, related_name='leaders')
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='iwi_leaderships')
    class Meta:
        unique_together = ('iwi', 'user')

class HapuLeader(models.Model):
    hapu = models.ForeignKey(Hapu, on_delete=models.CASCADE, related_name='leaders')
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='hapu_leaderships')
    class Meta:
        unique_together = ('hapu', 'user')
