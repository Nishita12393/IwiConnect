from django.test import TestCase
from django.utils import timezone
from core.models import CustomUser, Iwi, Hapu
from .models import Proposal, VotingOption, ProposalRecipient, Vote, ProposalComment
from .forms import ProposalForm
from datetime import timedelta
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client

# Create your tests here.

class ConsultationModelTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(email='testuser@example.com', password='testpass', full_name='Test User', state='VERIFIED')
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi description')
        self.hapu = Hapu.objects.create(name='Test Hapu', description='Test Hapu description', iwi=self.iwi)

    def test_proposal_creation_public(self):
        proposal = Proposal.objects.create(
            title='Public Consultation',
            description='A public consultation.',
            consultation_type='PUBLIC',
            start_date=timezone.now() + timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=2),
            created_by=self.user
        )
        self.assertEqual(proposal.consultation_type, 'PUBLIC')
        self.assertIsNone(proposal.iwi)
        self.assertIsNone(proposal.hapu)

    def test_proposal_creation_iwi(self):
        proposal = Proposal.objects.create(
            title='Iwi Consultation',
            description='An iwi consultation.',
            consultation_type='IWI',
            iwi=self.iwi,
            start_date=timezone.now() + timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=2),
            created_by=self.user
        )
        self.assertEqual(proposal.consultation_type, 'IWI')
        self.assertEqual(proposal.iwi, self.iwi)
        self.assertIsNone(proposal.hapu)

    def test_proposal_creation_hapu(self):
        proposal = Proposal.objects.create(
            title='Hapu Consultation',
            description='A hapu consultation.',
            consultation_type='HAPU',
            iwi=self.iwi,
            hapu=self.hapu,
            start_date=timezone.now() + timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=2),
            created_by=self.user
        )
        self.assertEqual(proposal.consultation_type, 'HAPU')
        self.assertEqual(proposal.iwi, self.iwi)
        self.assertEqual(proposal.hapu, self.hapu)

    def test_voting_option_creation(self):
        proposal = Proposal.objects.create(
            title='Vote Test',
            description='Test voting options.',
            consultation_type='PUBLIC',
            start_date=timezone.now() + timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=2),
            created_by=self.user
        )
        option1 = VotingOption.objects.create(proposal=proposal, text='Yes')
        option2 = VotingOption.objects.create(proposal=proposal, text='No')
        self.assertEqual(proposal.voting_options.count(), 2)
        self.assertIn(option1, proposal.voting_options.all())
        self.assertIn(option2, proposal.voting_options.all())

    def test_proposal_recipient_creation(self):
        proposal = Proposal.objects.create(
            title='Recipient Test',
            description='Test recipients.',
            consultation_type='PUBLIC',
            start_date=timezone.now() + timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=2),
            created_by=self.user
        )
        recipient = ProposalRecipient.objects.create(proposal=proposal, user=self.user)
        self.assertEqual(proposal.recipients.count(), 1)
        self.assertEqual(recipient.user, self.user)

    def test_vote_creation_and_uniqueness(self):
        proposal = Proposal.objects.create(
            title='Vote Uniqueness',
            description='Test vote uniqueness.',
            consultation_type='PUBLIC',
            start_date=timezone.now() + timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=2),
            created_by=self.user
        )
        option = VotingOption.objects.create(proposal=proposal, text='Yes')
        vote = Vote.objects.create(proposal=proposal, user=self.user, voting_option=option)
        self.assertEqual(proposal.votes.count(), 1)
        # Test uniqueness constraint
        with self.assertRaises(Exception):
            Vote.objects.create(proposal=proposal, user=self.user, voting_option=option)

    def test_proposal_comment_creation_and_approval(self):
        proposal = Proposal.objects.create(
            title='Comment Test',
            description='Test comments.',
            consultation_type='PUBLIC',
            start_date=timezone.now() + timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=2),
            created_by=self.user
        )
        comment = ProposalComment.objects.create(proposal=proposal, user=self.user, text='A comment.', is_approved=True)
        self.assertEqual(proposal.comments.count(), 1)
        self.assertTrue(comment.is_approved)

class ProposalFormTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(email='formuser@example.com', password='testpass', full_name='Form User', state='VERIFIED')
        self.iwi = Iwi.objects.create(name='Form Iwi', description='Form Iwi description')
        self.hapu = Hapu.objects.create(name='Form Hapu', description='Form Hapu description', iwi=self.iwi)
        self.future_start = timezone.now() + timedelta(days=2)
        self.future_end = self.future_start + timedelta(days=1)

    def get_valid_data(self, **overrides):
        data = {
            'title': 'Valid Consultation',
            'description': 'A valid consultation description with enough length.',
            'consultation_type': 'PUBLIC',
            'iwi': '',
            'hapu': '',
            'start_date': self.future_start.strftime('%Y-%m-%dT%H:%M'),
            'end_date': self.future_end.strftime('%Y-%m-%dT%H:%M'),
            'enable_comments': True,
            'anonymous_feedback': False,
            'is_draft': False,
            'voting_options': 'Yes\nNo',
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = ProposalForm(data=self.get_valid_data())
        self.assertTrue(form.is_valid())

    def test_title_too_short(self):
        data = self.get_valid_data(title='abc')
        form = ProposalForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_description_too_short(self):
        data = self.get_valid_data(description='short')
        form = ProposalForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)

    def test_not_enough_voting_options(self):
        data = self.get_valid_data(voting_options='Yes')
        form = ProposalForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('voting_options', form.errors)

    def test_start_date_in_past(self):
        data = self.get_valid_data(start_date=(timezone.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'))
        form = ProposalForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('start_date', form.errors)

    def test_end_date_in_past(self):
        data = self.get_valid_data(end_date=(timezone.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'))
        form = ProposalForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)

    def test_end_date_before_start_date(self):
        start = self.future_start
        end = self.future_start - timedelta(hours=1)
        data = self.get_valid_data(start_date=start.strftime('%Y-%m-%dT%H:%M'), end_date=end.strftime('%Y-%m-%dT%H:%M'))
        form = ProposalForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)

    def test_minimum_duration(self):
        start = self.future_start
        end = self.future_start + timedelta(minutes=30)
        data = self.get_valid_data(start_date=start.strftime('%Y-%m-%dT%H:%M'), end_date=end.strftime('%Y-%m-%dT%H:%M'))
        form = ProposalForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)

    def test_archived_iwi(self):
        self.iwi.is_archived = True
        self.iwi.save()
        data = self.get_valid_data(consultation_type='IWI', iwi=str(self.iwi.id))
        form = ProposalForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('iwi', form.errors)

    def test_archived_hapu(self):
        self.hapu.is_archived = True
        self.hapu.save()
        data = self.get_valid_data(consultation_type='HAPU', iwi=str(self.iwi.id), hapu=str(self.hapu.id))
        form = ProposalForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('hapu', form.errors)

    def test_draft_mode(self):
        data = self.get_valid_data(is_draft=True)
        form = ProposalForm(data=data)
        self.assertTrue(form.is_valid())

class ConsultationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(email='viewuser@example.com', password='testpass', full_name='View User', state='VERIFIED')
        self.staff = get_user_model().objects.create_user(email='admin@example.com', password='adminpass', full_name='Admin User', state='VERIFIED', is_staff=True)
        self.iwi = Iwi.objects.create(name='View Iwi', description='View Iwi description')
        self.hapu = Hapu.objects.create(name='View Hapu', description='View Hapu description', iwi=self.iwi)
        self.future_start = timezone.now() + timedelta(days=2)
        self.future_end = self.future_start + timedelta(days=1)

    def test_create_proposal_get(self):
        self.client.force_login(self.user)
        url = reverse('consultation:create_proposal')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New Consultation')

    def test_create_proposal_post_valid(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_login(self.user)
        url = reverse('consultation:create_proposal')
        data = {
            'title': 'View Test Consultation',
            'description': 'A valid consultation for view test.',
            'consultation_type': 'PUBLIC',
            'iwi': '',
            'hapu': '',
            'start_date': self.future_start.strftime('%Y-%m-%dT%H:%M'),
            'end_date': self.future_end.strftime('%Y-%m-%dT%H:%M'),
            'enable_comments': True,
            'anonymous_feedback': False,
            'is_draft': False,
            'voting_options': 'Yes\nNo',
        }
        response = self.client.post(url, data)
        if response.status_code != 302:
            print('Form errors:', response.context['form'].errors)
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertTrue(Proposal.objects.filter(title='View Test Consultation').exists())

    def test_create_proposal_post_invalid(self):
        self.client.force_login(self.user)
        url = reverse('consultation:create_proposal')
        data = {
            'title': 'abc',  # Too short
            'description': 'short',  # Too short
            'consultation_type': 'PUBLIC',
            'iwi': '',
            'hapu': '',
            'start_date': (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'end_date': (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'enable_comments': True,
            'anonymous_feedback': False,
            'is_draft': False,
            'voting_options': 'Yes',  # Not enough options
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please correct the errors below')
        self.assertFalse(Proposal.objects.filter(title='abc').exists())

    def test_active_consultations_staff(self):
        self.client.force_login(self.staff)
        Proposal.objects.create(
            title='Staff Consultation',
            description='Staff can see this.',
            consultation_type='PUBLIC',
            start_date=self.future_start,
            end_date=self.future_end,
            created_by=self.staff,
            is_draft=False
        )
        url = reverse('consultation:active_consultations')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Staff Consultation')

    def test_active_consultations_regular_user(self):
        self.client.force_login(self.user)
        Proposal.objects.create(
            title='User Consultation',
            description='User can see this.',
            consultation_type='PUBLIC',
            start_date=self.future_start,
            end_date=self.future_end,
            created_by=self.user,
            is_draft=False
        )
        url = reverse('consultation:active_consultations')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Consultation')

    def create_proposal_with_options(self, user=None, enable_comments=False, anonymous_feedback=False, is_draft=False, start_date=None, end_date=None):
        if user is None:
            user = self.user
        if start_date is None:
            start_date = self.future_start
        if end_date is None:
            end_date = self.future_end
        proposal = Proposal.objects.create(
            title='Detail Test',
            description='Detail view test.',
            consultation_type='PUBLIC',
            start_date=start_date,
            end_date=end_date,
            created_by=user,
            enable_comments=enable_comments,
            anonymous_feedback=anonymous_feedback,
            is_draft=is_draft
        )
        option1 = VotingOption.objects.create(proposal=proposal, text='Yes')
        option2 = VotingOption.objects.create(proposal=proposal, text='No')
        return proposal, option1, option2

    def test_member_consultation_detail_get_staff(self):
        self.client.force_login(self.staff)
        proposal, _, _ = self.create_proposal_with_options(user=self.staff)
        url = reverse('consultation:member_consultation_detail', args=[proposal.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, proposal.title)

    def test_member_consultation_detail_get_regular_user(self):
        self.client.force_login(self.user)
        proposal, _, _ = self.create_proposal_with_options()
        url = reverse('consultation:member_consultation_detail', args=[proposal.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, proposal.title)

    def test_member_consultation_detail_vote(self):
        self.client.force_login(self.user)
        now = timezone.now()
        proposal, option1, _ = self.create_proposal_with_options(start_date=now - timedelta(days=1), end_date=now + timedelta(days=1))
        url = reverse('consultation:member_consultation_detail', args=[proposal.pk])
        # First vote
        response = self.client.post(url, {'voting_option': str(option1.pk)})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Vote.objects.filter(proposal=proposal, user=self.user, voting_option=option1).exists())
        # Duplicate vote
        response = self.client.post(url, {'voting_option': str(option1.pk)})
        self.assertEqual(response.status_code, 302)
        votes = Vote.objects.filter(proposal=proposal, user=self.user)
        self.assertEqual(votes.count(), 1)

    def test_member_consultation_detail_comment(self):
        self.client.force_login(self.user)
        now = timezone.now()
        proposal, option1, _ = self.create_proposal_with_options(enable_comments=True, start_date=now - timedelta(days=1), end_date=now + timedelta(days=1))
        url = reverse('consultation:member_consultation_detail', args=[proposal.pk])
        response = self.client.post(url, {'voting_option': str(option1.pk), 'comment': 'A test comment.'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ProposalComment.objects.filter(proposal=proposal, text='A test comment.').exists())

    def test_member_consultation_detail_comment_anonymous(self):
        self.client.force_login(self.user)
        now = timezone.now()
        proposal, option1, _ = self.create_proposal_with_options(enable_comments=True, anonymous_feedback=True, start_date=now - timedelta(days=1), end_date=now + timedelta(days=1))
        url = reverse('consultation:member_consultation_detail', args=[proposal.pk])
        response = self.client.post(url, {'voting_option': str(option1.pk), 'comment': 'Anon comment.'})
        self.assertEqual(response.status_code, 302)
        comment = ProposalComment.objects.filter(proposal=proposal, text='Anon comment.').first()
        self.assertIsNotNone(comment)
        self.assertIsNone(comment.user)

    def test_consultation_result_staff(self):
        self.client.force_login(self.staff)
        now = timezone.now()
        proposal, option1, option2 = self.create_proposal_with_options(user=self.staff, start_date=now - timedelta(days=2), end_date=now - timedelta(days=1))
        # Add votes
        Vote.objects.create(proposal=proposal, user=self.staff, voting_option=option1)
        Vote.objects.create(proposal=proposal, user=self.user, voting_option=option2)
        url = reverse('consultation:consultation_result', args=[proposal.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, proposal.title)
        self.assertContains(response, option1.text)
        self.assertContains(response, option2.text)
        self.assertContains(response, '50.00%')  # Should show percentages

    def test_consultation_result_regular_user_access(self):
        self.client.force_login(self.user)
        now = timezone.now()
        proposal, option1, option2 = self.create_proposal_with_options(start_date=now - timedelta(days=2), end_date=now - timedelta(days=1))
        Vote.objects.create(proposal=proposal, user=self.user, voting_option=option1)
        url = reverse('consultation:consultation_result', args=[proposal.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, proposal.title)
        self.assertContains(response, option1.text)
        self.assertContains(response, option2.text)

    def test_consultation_result_access_denied(self):
        # Create an IWI-restricted proposal, user not in iwi
        other_iwi = Iwi.objects.create(name='Other Iwi', description='Other')
        proposal = Proposal.objects.create(
            title='Restricted',
            description='Restricted result.',
            consultation_type='IWI',
            iwi=other_iwi,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() - timedelta(days=1),
            created_by=self.staff,
            is_draft=False
        )
        self.client.force_login(self.user)
        url = reverse('consultation:consultation_result', args=[proposal.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
