from django.db import models
from core.models import CustomUser, Iwi, Hapu

# Create your models here.

class Proposal(models.Model):
    CONSULTATION_TYPE_CHOICES = [
        ('PUBLIC', 'Public'),
        ('IWI', 'Restricted to Iwi'),
        ('HAPU', 'Restricted to Hapu'),
    ]
    title = models.CharField(max_length=255)
    description = models.TextField()
    consultation_type = models.CharField(max_length=10, choices=CONSULTATION_TYPE_CHOICES)
    iwi = models.ForeignKey(Iwi, null=True, blank=True, on_delete=models.SET_NULL)
    hapu = models.ForeignKey(Hapu, null=True, blank=True, on_delete=models.SET_NULL)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    enable_comments = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='proposals')
    anonymous_feedback = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class VotingOption(models.Model):
    proposal = models.ForeignKey(Proposal, related_name='voting_options', on_delete=models.CASCADE)
    text = models.CharField(max_length=100)

class ProposalRecipient(models.Model):
    proposal = models.ForeignKey(Proposal, related_name='recipients', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

class Vote(models.Model):
    proposal = models.ForeignKey(Proposal, related_name='votes', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL)
    voting_option = models.ForeignKey(VotingOption, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('proposal', 'user')

class ProposalComment(models.Model):
    proposal = models.ForeignKey(Proposal, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
