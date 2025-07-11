from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Iwi, Hapu, IwiLeader, HapuLeader
from .models import Event, EventParticipant

User = get_user_model()


class EventModelTestCase(TestCase):
    """Test cases for Event model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Test User',
            state='VERIFIED'
        )
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi description')
        self.hapu = Hapu.objects.create(name='Test Hapu', description='Test Hapu description', iwi=self.iwi)

    def test_event_creation(self):
        """Test creating an Event"""
        start_time = timezone.now() + timezone.timedelta(hours=1)
        end_time = start_time + timezone.timedelta(hours=2)
        
        event = Event.objects.create(
            title='Test Event',
            description='This is a test event description.',
            start_datetime=start_time,
            end_datetime=end_time,
            location_type='PHYSICAL',
            location='Test Location',
            visibility='PUBLIC',
            created_by=self.user
        )
        
        self.assertEqual(event.title, 'Test Event')
        self.assertEqual(event.description, 'This is a test event description.')
        self.assertEqual(event.location_type, 'PHYSICAL')
        self.assertEqual(event.location, 'Test Location')
        self.assertEqual(event.visibility, 'PUBLIC')
        self.assertEqual(event.created_by, self.user)
        self.assertIsNone(event.iwi)
        self.assertIsNone(event.hapu)
        self.assertEqual(event.online_url, '')

    def test_event_string_representation(self):
        """Test the string representation of an Event"""
        start_time = timezone.now() + timezone.timedelta(hours=1)
        end_time = start_time + timezone.timedelta(hours=2)
        
        event = Event.objects.create(
            title='Test Event Title',
            description='Test description',
            start_datetime=start_time,
            end_datetime=end_time,
            created_by=self.user
        )
        
        self.assertEqual(str(event), 'Test Event Title')

    def test_event_with_iwi_visibility(self):
        """Test creating an Event with Iwi-specific visibility"""
        start_time = timezone.now() + timezone.timedelta(hours=1)
        end_time = start_time + timezone.timedelta(hours=2)
        
        event = Event.objects.create(
            title='Iwi Event',
            description='Iwi-specific event',
            start_datetime=start_time,
            end_datetime=end_time,
            visibility='IWI',
            iwi=self.iwi,
            created_by=self.user
        )
        
        self.assertEqual(event.visibility, 'IWI')
        self.assertEqual(event.iwi, self.iwi)
        self.assertIsNone(event.hapu)

    def test_event_with_hapu_visibility(self):
        """Test creating an Event with Hapu-specific visibility"""
        start_time = timezone.now() + timezone.timedelta(hours=1)
        end_time = start_time + timezone.timedelta(hours=2)
        
        event = Event.objects.create(
            title='Hapu Event',
            description='Hapu-specific event',
            start_datetime=start_time,
            end_datetime=end_time,
            visibility='HAPU',
            iwi=self.iwi,
            hapu=self.hapu,
            created_by=self.user
        )
        
        self.assertEqual(event.visibility, 'HAPU')
        self.assertEqual(event.iwi, self.iwi)
        self.assertEqual(event.hapu, self.hapu)

    def test_online_event(self):
        """Test creating an online Event"""
        start_time = timezone.now() + timezone.timedelta(hours=1)
        end_time = start_time + timezone.timedelta(hours=2)
        
        event = Event.objects.create(
            title='Online Event',
            description='Online event description',
            start_datetime=start_time,
            end_datetime=end_time,
            location_type='ONLINE',
            online_url='https://example.com/meeting',
            visibility='PUBLIC',
            created_by=self.user
        )
        
        self.assertEqual(event.location_type, 'ONLINE')
        self.assertEqual(event.online_url, 'https://example.com/meeting')
        self.assertEqual(event.location, '')

    def test_event_ordering(self):
        """Test that Events are ordered by start_datetime"""
        now = timezone.now()
        event1 = Event.objects.create(
            title='Later Event',
            description='Later event',
            start_datetime=now + timezone.timedelta(hours=3),
            end_datetime=now + timezone.timedelta(hours=4),
            created_by=self.user
        )
        event2 = Event.objects.create(
            title='Earlier Event',
            description='Earlier event',
            start_datetime=now + timezone.timedelta(hours=1),
            end_datetime=now + timezone.timedelta(hours=2),
            created_by=self.user
        )
        
        events = Event.objects.order_by('start_datetime')
        self.assertEqual(events[0], event2)  # Earlier event first
        self.assertEqual(events[1], event1)  # Later event second


class EventParticipantModelTestCase(TestCase):
    """Test cases for EventParticipant model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='userpass123',
            full_name='User One',
            state='VERIFIED'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='userpass123',
            full_name='User Two',
            state='VERIFIED'
        )
        
        start_time = timezone.now() + timezone.timedelta(hours=1)
        end_time = start_time + timezone.timedelta(hours=2)
        
        self.event = Event.objects.create(
            title='Test Event',
            description='Test event description',
            start_datetime=start_time,
            end_datetime=end_time,
            created_by=self.user1
        )

    def test_event_participant_creation(self):
        """Test creating an EventParticipant"""
        participant = EventParticipant.objects.create(
            event=self.event,
            user=self.user2
        )
        
        self.assertEqual(participant.event, self.event)
        self.assertEqual(participant.user, self.user2)
        self.assertIsNotNone(participant.joined_at)

    def test_event_participant_unique_constraint(self):
        """Test that a user cannot join the same event twice"""
        EventParticipant.objects.create(event=self.event, user=self.user2)
        
        # Try to create another participant for the same event and user
        with self.assertRaises(Exception):  # Should raise IntegrityError
            EventParticipant.objects.create(event=self.event, user=self.user2)

    def test_event_participant_get_or_create(self):
        """Test get_or_create for EventParticipant"""
        # First time - should create
        participant, created = EventParticipant.objects.get_or_create(
            event=self.event,
            user=self.user2
        )
        self.assertTrue(created)
        self.assertEqual(participant.event, self.event)
        self.assertEqual(participant.user, self.user2)
        
        # Second time - should get existing
        participant2, created2 = EventParticipant.objects.get_or_create(
            event=self.event,
            user=self.user2
        )
        self.assertFalse(created2)
        self.assertEqual(participant2, participant)

    def test_event_participant_relationship(self):
        """Test the relationship between Event and EventParticipant"""
        participant = EventParticipant.objects.create(
            event=self.event,
            user=self.user2
        )
        
        # Test reverse relationship
        self.assertIn(participant, self.event.participants.all())
        self.assertEqual(self.event.participants.count(), 1)
        
        # Test forward relationship
        self.assertEqual(participant.event, self.event)


class EventFormTestCase(TestCase):
    """Test cases for EventForm validation"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Test User',
            state='VERIFIED'
        )
        self.user.is_staff = True
        self.user.save()
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi description')
        self.hapu = Hapu.objects.create(name='Test Hapu', description='Test Hapu description', iwi=self.iwi)
        # Make user a leader to have permissions for Iwi/Hapu events
        IwiLeader.objects.create(user=self.user, iwi=self.iwi)

    def test_event_form_valid_physical_event(self):
        """Test EventForm with valid physical event data"""
        # Use a future date to avoid 'start_datetime in the past' errors
        start_time = timezone.now() + timezone.timedelta(days=1, hours=2)
        end_time = start_time + timezone.timedelta(hours=2)
        
        from .forms import EventForm
        
        data = {
            'title': 'Valid Physical Event',
            'description': 'This is a valid physical event description with enough characters.',
            'start_datetime': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end_time.strftime('%Y-%m-%dT%H:%M'),
            'location_type': 'PHYSICAL',
            'location': 'Test Location Address',
            'visibility': 'PUBLIC'
        }
        
        form = EventForm(data, user=self.user)
        if not form.is_valid():
            print("Form errors:", form.errors)
            print("Start time:", start_time)
            print("Current time:", timezone.now())
        self.assertTrue(form.is_valid())

    def test_event_form_valid_online_event(self):
        """Test EventForm with valid online event data"""
        start_time = timezone.now() + timezone.timedelta(days=1, hours=2)
        end_time = start_time + timezone.timedelta(hours=2)
        
        from .forms import EventForm
        
        data = {
            'title': 'Valid Online Event',
            'description': 'This is a valid online event description with enough characters.',
            'start_datetime': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end_time.strftime('%Y-%m-%dT%H:%M'),
            'location_type': 'ONLINE',
            'online_url': 'https://example.com/meeting',
            'visibility': 'PUBLIC'
        }
        
        form = EventForm(data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_event_form_valid_iwi_event(self):
        """Test EventForm with valid Iwi-specific event data"""
        start_time = timezone.now() + timezone.timedelta(days=1, hours=2)
        end_time = start_time + timezone.timedelta(hours=2)
        
        from .forms import EventForm
        
        data = {
            'title': 'Valid Iwi Event',
            'description': 'This is a valid Iwi event description with enough characters.',
            'start_datetime': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end_time.strftime('%Y-%m-%dT%H:%M'),
            'location_type': 'PHYSICAL',
            'location': 'Test Location',
            'visibility': 'IWI',
            'iwi': str(self.iwi.id)
        }
        
        form = EventForm(data, user=self.user)
        if not form.is_valid():
            print("Iwi event form errors:", form.errors)
            print("Iwi field queryset:", form.fields['iwi'].queryset)
            print("User iwi leaderships:", list(self.user.iwi_leaderships.values_list('iwi_id', flat=True)))
            print("Provided iwi ID:", self.iwi.id)
            print("Form data:", form.data)
            print("Form cleaned_data:", getattr(form, 'cleaned_data', None))
        self.assertTrue(form.is_valid())

    def test_event_form_valid_hapu_event(self):
        """Test EventForm with valid Hapu-specific event data"""
        start_time = timezone.now() + timezone.timedelta(days=1, hours=2)
        end_time = start_time + timezone.timedelta(hours=2)
        
        from .forms import EventForm
        
        data = {
            'title': 'Valid Hapu Event',
            'description': 'This is a valid Hapu event description with enough characters.',
            'start_datetime': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end_time.strftime('%Y-%m-%dT%H:%M'),
            'location_type': 'PHYSICAL',
            'location': 'Test Location',
            'visibility': 'HAPU',
            'iwi': str(self.iwi.id),
            'hapu': str(self.hapu.id)
        }
        
        form = EventForm(data, user=self.user)
        if not form.is_valid():
            print("Hapu event form errors:", form.errors)
            print("Hapu field queryset:", form.fields['hapu'].queryset)
            print("User hapu leaderships:", list(self.user.hapu_leaderships.values_list('hapu_id', flat=True)))
            print("Provided hapu ID:", self.hapu.id)
            print("Form data:", form.data)
            print("Form cleaned_data:", getattr(form, 'cleaned_data', None))
        self.assertTrue(form.is_valid())

    def test_event_form_title_validation(self):
        """Test EventForm title validation"""
        start_time = timezone.now() + timezone.timedelta(days=1, hours=2)
        end_time = start_time + timezone.timedelta(hours=2)
        
        from .forms import EventForm
        
        # Test too short title
        data = {
            'title': 'Hi',
            'description': 'Valid description with enough characters.',
            'start_datetime': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end_time.strftime('%Y-%m-%dT%H:%M'),
            'location_type': 'PHYSICAL',
            'location': 'Test Location',
            'visibility': 'PUBLIC'
        }
        
        form = EventForm(data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_event_form_description_validation(self):
        """Test EventForm description validation"""
        start_time = timezone.now() + timezone.timedelta(days=1, hours=2)
        end_time = start_time + timezone.timedelta(hours=2)
        
        from .forms import EventForm
        
        # Test too short description
        data = {
            'title': 'Valid Title',
            'description': 'Short',
            'start_datetime': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end_time.strftime('%Y-%m-%dT%H:%M'),
            'location_type': 'PHYSICAL',
            'location': 'Test Location',
            'visibility': 'PUBLIC'
        }
        
        form = EventForm(data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)

    def test_event_form_location_validation(self):
        """Test EventForm location validation for physical events"""
        start_time = timezone.now() + timezone.timedelta(days=1, hours=2)
        end_time = start_time + timezone.timedelta(hours=2)
        
        from .forms import EventForm
        
        # Test missing location for physical event
        data = {
            'title': 'Valid Title',
            'description': 'Valid description with enough characters.',
            'start_datetime': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end_time.strftime('%Y-%m-%dT%H:%M'),
            'location_type': 'PHYSICAL',
            'location': '',
            'visibility': 'PUBLIC'
        }
        
        form = EventForm(data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('location', form.errors)

    def test_event_form_online_url_validation(self):
        """Test EventForm online URL validation for online events"""
        start_time = timezone.now() + timezone.timedelta(days=1, hours=2)
        end_time = start_time + timezone.timedelta(hours=2)
        
        from .forms import EventForm
        
        # Test missing online URL for online event
        data = {
            'title': 'Valid Title',
            'description': 'Valid description with enough characters.',
            'start_datetime': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end_time.strftime('%Y-%m-%dT%H:%M'),
            'location_type': 'ONLINE',
            'online_url': '',
            'visibility': 'PUBLIC'
        }
        
        form = EventForm(data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('online_url', form.errors)

    def test_event_form_datetime_validation(self):
        """Test EventForm datetime validation"""
        past_time = timezone.now() - timezone.timedelta(hours=1)
        future_time = timezone.now() + timezone.timedelta(hours=1)
        
        from .forms import EventForm
        
        # Test past start time
        data = {
            'title': 'Valid Title',
            'description': 'Valid description with enough characters.',
            'start_datetime': past_time.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': future_time.strftime('%Y-%m-%dT%H:%M'),
            'location_type': 'PHYSICAL',
            'location': 'Test Location',
            'visibility': 'PUBLIC'
        }
        
        form = EventForm(data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('start_datetime', form.errors)

    def test_event_form_visibility_validation(self):
        """Test EventForm visibility validation"""
        start_time = timezone.now() + timezone.timedelta(days=1, hours=2)
        end_time = start_time + timezone.timedelta(hours=2)
        
        from .forms import EventForm
        
        # Test Iwi visibility without Iwi
        data = {
            'title': 'Valid Title',
            'description': 'Valid description with enough characters.',
            'start_datetime': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end_time.strftime('%Y-%m-%dT%H:%M'),
            'location_type': 'PHYSICAL',
            'location': 'Test Location',
            'visibility': 'IWI'
        }
        
        form = EventForm(data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('visibility', form.errors)

    def test_event_form_attachment_validation(self):
        """Test EventForm attachment validation"""
        start_time = timezone.now() + timezone.timedelta(days=1, hours=2)
        end_time = start_time + timezone.timedelta(hours=2)
        
        from .forms import EventForm
        
        # Test invalid file type
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"file_content",
            content_type="text/plain"
        )
        
        data = {
            'title': 'Valid Title',
            'description': 'Valid description with enough characters.',
            'start_datetime': start_time.strftime('%Y-%m-%dT%H:%M'),
            'end_datetime': end_time.strftime('%Y-%m-%dT%H:%M'),
            'location_type': 'PHYSICAL',
            'location': 'Test Location',
            'visibility': 'PUBLIC'
        }
        
        files = {
            'attachment': invalid_file
        }
        
        form = EventForm(data, files, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('attachment', form.errors)
