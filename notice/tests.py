from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages
from django.utils import timezone
from datetime import timedelta
from .models import Notice, NoticeAcknowledgment
from core.models import Iwi, Hapu

User = get_user_model()


class NoticeModelTestCase(TestCase):
    """Test cases for Notice model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi Description')
        self.hapu = Hapu.objects.create(name='Test Hapu', iwi=self.iwi, description='Test Hapu Description')
        
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            is_staff=True,
            state='VERIFIED'
        )
        
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Regular User',
            state='VERIFIED'
        )
        
        self.future_date = timezone.now() + timedelta(days=7)
        self.past_date = timezone.now() - timedelta(days=1)

    def test_notice_creation(self):
        """Test creating a notice"""
        notice = Notice.objects.create(
            title='Test Notice',
            content='This is a test notice content.',
            expiry_date=self.future_date,
            audience='ALL',
            created_by=self.admin_user,
            priority=5
        )
        
        self.assertEqual(notice.title, 'Test Notice')
        self.assertEqual(notice.content, 'This is a test notice content.')
        self.assertEqual(notice.audience, 'ALL')
        self.assertEqual(notice.created_by, self.admin_user)
        self.assertEqual(notice.priority, 5)
        self.assertTrue(notice.is_active())

    def test_notice_is_active_future_date(self):
        """Test that notice is active when expiry date is in the future"""
        notice = Notice.objects.create(
            title='Future Notice',
            content='This notice expires in the future.',
            expiry_date=self.future_date,
            audience='ALL',
            created_by=self.admin_user
        )
        self.assertTrue(notice.is_active())

    def test_notice_is_not_active_past_date(self):
        """Test that notice is not active when expiry date is in the past"""
        notice = Notice.objects.create(
            title='Past Notice',
            content='This notice has expired.',
            expiry_date=self.past_date,
            audience='ALL',
            created_by=self.admin_user
        )
        self.assertFalse(notice.is_active())

    def test_notice_string_representation(self):
        """Test the string representation of a notice"""
        notice = Notice.objects.create(
            title='Test Notice Title',
            content='Test content',
            expiry_date=self.future_date,
            audience='ALL',
            created_by=self.admin_user
        )
        self.assertEqual(str(notice), 'Test Notice Title')

    def test_notice_with_iwi_audience(self):
        """Test creating a notice for specific Iwi"""
        notice = Notice.objects.create(
            title='Iwi Notice',
            content='This notice is for a specific Iwi.',
            expiry_date=self.future_date,
            audience='IWI',
            iwi=self.iwi,
            created_by=self.admin_user
        )
        
        self.assertEqual(notice.audience, 'IWI')
        self.assertEqual(notice.iwi, self.iwi)
        self.assertIsNone(notice.hapu)

    def test_notice_with_hapu_audience(self):
        """Test creating a notice for specific Hapu"""
        notice = Notice.objects.create(
            title='Hapu Notice',
            content='This notice is for a specific Hapu.',
            expiry_date=self.future_date,
            audience='HAPU',
            iwi=self.iwi,
            hapu=self.hapu,
            created_by=self.admin_user
        )
        
        self.assertEqual(notice.audience, 'HAPU')
        self.assertEqual(notice.iwi, self.iwi)
        self.assertEqual(notice.hapu, self.hapu)


class NoticeAcknowledgmentTestCase(TestCase):
    """Test cases for NoticeAcknowledgment model"""
    
    def setUp(self):
        """Set up test data"""
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi Description')
        
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            is_staff=True,
            state='VERIFIED'
        )
        
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
        
        self.notice = Notice.objects.create(
            title='Test Notice',
            content='Test content',
            expiry_date=timezone.now() + timedelta(days=7),
            audience='ALL',
            created_by=self.admin_user
        )

    def test_acknowledgment_creation(self):
        """Test creating a notice acknowledgment"""
        acknowledgment = NoticeAcknowledgment.objects.create(
            notice=self.notice,
            user=self.user1
        )
        
        self.assertEqual(acknowledgment.notice, self.notice)
        self.assertEqual(acknowledgment.user, self.user1)
        self.assertIsNotNone(acknowledgment.acknowledged_at)

    def test_unique_acknowledgment_constraint(self):
        """Test that a user can only acknowledge a notice once"""
        # Create first acknowledgment
        NoticeAcknowledgment.objects.create(
            notice=self.notice,
            user=self.user1
        )
        
        # Try to create duplicate acknowledgment
        with self.assertRaises(Exception):
            NoticeAcknowledgment.objects.create(
                notice=self.notice,
                user=self.user1
            )

    def test_multiple_users_can_acknowledge(self):
        """Test that multiple users can acknowledge the same notice"""
        acknowledgment1 = NoticeAcknowledgment.objects.create(
            notice=self.notice,
            user=self.user1
        )
        
        acknowledgment2 = NoticeAcknowledgment.objects.create(
            notice=self.notice,
            user=self.user2
        )
        
        self.assertEqual(self.notice.acknowledgments.count(), 2)
        self.assertIn(acknowledgment1, self.notice.acknowledgments.all())
        self.assertIn(acknowledgment2, self.notice.acknowledgments.all())


class NoticeFormTestCase(TestCase):
    """Test cases for NoticeForm validation"""
    
    def setUp(self):
        """Set up test data"""
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi Description')
        self.hapu = Hapu.objects.create(name='Test Hapu', iwi=self.iwi, description='Test Hapu Description')
        
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            is_staff=True,
            state='VERIFIED'
        )
        
        self.future_date = timezone.now() + timedelta(days=7)
        self.past_date = timezone.now() - timedelta(days=1)

    def test_valid_notice_form_all_audience(self):
        """Test valid notice form for all users audience"""
        from .forms import NoticeForm
        
        data = {
            'title': 'Valid Notice Title',
            'content': 'This is a valid notice content with enough characters to meet the minimum requirement.',
            'expiry_date': self.future_date.strftime('%Y-%m-%dT%H:%M'),
            'audience': 'ALL',
            'priority': 5
        }
        
        form = NoticeForm(data)
        self.assertTrue(form.is_valid())

    def test_valid_notice_form_iwi_audience(self):
        """Test valid notice form for Iwi audience"""
        from .forms import NoticeForm
        
        data = {
            'title': 'Valid Iwi Notice',
            'content': 'This is a valid notice content for a specific Iwi.',
            'expiry_date': self.future_date.strftime('%Y-%m-%dT%H:%M'),
            'audience': 'IWI',
            'iwi': self.iwi.id,
            'priority': 3
        }
        
        form = NoticeForm(data)
        self.assertTrue(form.is_valid())

    def test_valid_notice_form_hapu_audience(self):
        """Test valid notice form for Hapu audience"""
        from .forms import NoticeForm
        
        data = {
            'title': 'Valid Hapu Notice',
            'content': 'This is a valid notice content for a specific Hapu.',
            'expiry_date': self.future_date.strftime('%Y-%m-%dT%H:%M'),
            'audience': 'HAPU',
            'iwi': self.iwi.id,
            'hapu': self.hapu.id,
            'priority': 7
        }
        
        form = NoticeForm(data)
        self.assertTrue(form.is_valid())

    def test_invalid_title_too_short(self):
        """Test notice form with title too short"""
        from .forms import NoticeForm
        
        data = {
            'title': 'Hi',
            'content': 'This is a valid notice content with enough characters.',
            'expiry_date': self.future_date.strftime('%Y-%m-%dT%H:%M'),
            'audience': 'ALL',
            'priority': 5
        }
        
        form = NoticeForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_invalid_title_too_long(self):
        """Test notice form with title too long"""
        from .forms import NoticeForm
        
        data = {
            'title': 'A' * 201,  # 201 characters
            'content': 'This is a valid notice content with enough characters.',
            'expiry_date': self.future_date.strftime('%Y-%m-%dT%H:%M'),
            'audience': 'ALL',
            'priority': 5
        }
        
        form = NoticeForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_invalid_content_too_short(self):
        """Test notice form with content too short"""
        from .forms import NoticeForm
        
        data = {
            'title': 'Valid Title',
            'content': 'Short',
            'expiry_date': self.future_date.strftime('%Y-%m-%dT%H:%M'),
            'audience': 'ALL',
            'priority': 5
        }
        
        form = NoticeForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)

    def test_invalid_expiry_date_past(self):
        """Test notice form with expiry date in the past"""
        from .forms import NoticeForm
        
        data = {
            'title': 'Valid Title',
            'content': 'This is a valid notice content with enough characters.',
            'expiry_date': self.past_date.strftime('%Y-%m-%dT%H:%M'),
            'audience': 'ALL',
            'priority': 5
        }
        
        form = NoticeForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('expiry_date', form.errors)

    def test_invalid_priority_too_low(self):
        """Test notice form with priority too low"""
        from .forms import NoticeForm
        
        data = {
            'title': 'Valid Title',
            'content': 'This is a valid notice content with enough characters.',
            'expiry_date': self.future_date.strftime('%Y-%m-%dT%H:%M'),
            'audience': 'ALL',
            'priority': 0
        }
        
        form = NoticeForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('priority', form.errors)

    def test_invalid_priority_too_high(self):
        """Test notice form with priority too high"""
        from .forms import NoticeForm
        
        data = {
            'title': 'Valid Title',
            'content': 'This is a valid notice content with enough characters.',
            'expiry_date': self.future_date.strftime('%Y-%m-%dT%H:%M'),
            'audience': 'ALL',
            'priority': 11
        }
        
        form = NoticeForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('priority', form.errors)

    def test_invalid_all_audience_with_iwi(self):
        """Test notice form with ALL audience but Iwi selected"""
        from .forms import NoticeForm
        
        data = {
            'title': 'Valid Title',
            'content': 'This is a valid notice content with enough characters.',
            'expiry_date': self.future_date.strftime('%Y-%m-%dT%H:%M'),
            'audience': 'ALL',
            'iwi': self.iwi.id,
            'priority': 5
        }
        
        form = NoticeForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('iwi', form.errors)

    def test_invalid_iwi_audience_without_iwi(self):
        """Test notice form with IWI audience but no Iwi selected"""
        from .forms import NoticeForm
        
        data = {
            'title': 'Valid Title',
            'content': 'This is a valid notice content with enough characters.',
            'expiry_date': self.future_date.strftime('%Y-%m-%dT%H:%M'),
            'audience': 'IWI',
            'priority': 5
        }
        
        form = NoticeForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('iwi', form.errors)

    def test_invalid_hapu_audience_without_hapu(self):
        """Test notice form with HAPU audience but no Hapu selected"""
        from .forms import NoticeForm
        
        data = {
            'title': 'Valid Title',
            'content': 'This is a valid notice content with enough characters.',
            'expiry_date': self.future_date.strftime('%Y-%m-%dT%H:%M'),
            'audience': 'HAPU',
            'iwi': self.iwi.id,
            'priority': 5
        }
        
        form = NoticeForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('hapu', form.errors)


class NoticeListViewTestCase(TestCase):
    """Test cases for notice list view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.list_url = reverse('notice:notice_list')
        
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi Description')
        self.hapu = Hapu.objects.create(name='Test Hapu', iwi=self.iwi, description='Test Hapu Description')
        
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            is_staff=True,
            state='VERIFIED'
        )
        
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Regular User',
            state='VERIFIED'
        )
        
        self.future_date = timezone.now() + timedelta(days=7)
        self.past_date = timezone.now() - timedelta(days=1)
        
        # Create test notices
        self.active_notice = Notice.objects.create(
            title='Active Notice',
            content='This is an active notice.',
            expiry_date=self.future_date,
            audience='ALL',
            created_by=self.admin_user,
            priority=5
        )
        
        self.expired_notice = Notice.objects.create(
            title='Expired Notice',
            content='This notice has expired.',
            expiry_date=self.past_date,
            audience='ALL',
            created_by=self.admin_user,
            priority=3
        )
        
        self.iwi_notice = Notice.objects.create(
            title='Iwi Notice',
            content='This notice is for a specific Iwi.',
            expiry_date=self.future_date,
            audience='IWI',
            iwi=self.iwi,
            created_by=self.admin_user,
            priority=7
        )

    def test_notice_list_requires_login(self):
        """Test that notice list requires login"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 302)

    def test_notice_list_loads(self):
        """Test that notice list page loads correctly"""
        self.client.force_login(self.regular_user)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notice/notice_list.html')
        self.assertContains(response, 'Notice Board')
        self.assertContains(response, 'Active Notice')
        self.assertNotContains(response, 'Expired Notice')  # Should not show expired notices

    def test_notice_list_filter_by_audience(self):
        """Test filtering notices by audience"""
        self.client.force_login(self.regular_user)
        response = self.client.get(self.list_url + '?audience=IWI')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Iwi Notice')
        self.assertNotContains(response, 'Active Notice')

    def test_notice_list_filter_by_iwi(self):
        """Test filtering notices by Iwi"""
        self.client.force_login(self.regular_user)
        response = self.client.get(self.list_url + f'?iwi={self.iwi.id}')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Iwi Notice')
        self.assertNotContains(response, 'Active Notice')

    def test_notice_list_pagination(self):
        """Test notice list pagination"""
        # Create more notices to test pagination
        for i in range(10):
            Notice.objects.create(
                title=f'Notice {i}',
                content=f'Content for notice {i}',
                expiry_date=self.future_date,
                audience='ALL',
                created_by=self.admin_user,
                priority=5
            )
        
        self.client.force_login(self.regular_user)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['page_obj'].has_other_pages())


class NoticeDetailViewTestCase(TestCase):
    """Test cases for notice detail view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi Description')
        self.hapu = Hapu.objects.create(name='Test Hapu', iwi=self.iwi, description='Test Hapu Description')
        
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            is_staff=True,
            state='VERIFIED'
        )
        
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Regular User',
            state='VERIFIED'
        )
        
        self.notice = Notice.objects.create(
            title='Test Notice',
            content='This is a test notice content.',
            expiry_date=timezone.now() + timedelta(days=7),
            audience='ALL',
            created_by=self.admin_user,
            priority=5
        )
        
        self.detail_url = reverse('notice:notice_detail', kwargs={'pk': self.notice.pk})

    def test_notice_detail_requires_login(self):
        """Test that notice detail requires login"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 302)

    def test_notice_detail_loads(self):
        """Test that notice detail page loads correctly"""
        self.client.force_login(self.regular_user)
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notice/notice_detail.html')
        self.assertContains(response, 'Test Notice')
        self.assertContains(response, 'This is a test notice content.')

    def test_notice_detail_creates_acknowledgment(self):
        """Test that viewing notice detail creates an acknowledgment"""
        self.client.force_login(self.regular_user)
        
        # Check no acknowledgment exists initially
        self.assertFalse(NoticeAcknowledgment.objects.filter(notice=self.notice, user=self.regular_user).exists())
        
        # View the notice
        response = self.client.get(self.detail_url)
        
        # Check acknowledgment was created
        self.assertTrue(NoticeAcknowledgment.objects.filter(notice=self.notice, user=self.regular_user).exists())

    def test_notice_detail_duplicate_acknowledgment(self):
        """Test that viewing notice detail doesn't create duplicate acknowledgments"""
        self.client.force_login(self.regular_user)
        
        # Create acknowledgment first
        NoticeAcknowledgment.objects.create(notice=self.notice, user=self.regular_user)
        initial_count = NoticeAcknowledgment.objects.filter(notice=self.notice, user=self.regular_user).count()
        
        # View the notice again
        response = self.client.get(self.detail_url)
        
        # Check no duplicate acknowledgment was created
        final_count = NoticeAcknowledgment.objects.filter(notice=self.notice, user=self.regular_user).count()
        self.assertEqual(initial_count, final_count)

    def test_notice_detail_not_found(self):
        """Test notice detail with non-existent notice"""
        self.client.force_login(self.regular_user)
        response = self.client.get(reverse('notice:notice_detail', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)


class NoticeCreateViewTestCase(TestCase):
    """Test cases for notice creation view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.create_url = reverse('notice:create_notice')
        
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi Description')
        self.hapu = Hapu.objects.create(name='Test Hapu', iwi=self.iwi, description='Test Hapu Description')
        
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            is_staff=True,
            state='VERIFIED'
        )
        
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Regular User',
            state='VERIFIED'
        )
        
        self.future_date = timezone.now() + timedelta(days=7)

    def test_create_notice_requires_leader_or_admin(self):
        """Test that create notice requires leader or admin access"""
        # Not logged in
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 302)
        
        # Regular user (not leader or admin)
        self.client.force_login(self.regular_user)
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 302)  # Redirects for non-leaders/admins

    def test_create_notice_admin_access(self):
        """Test that admin can access create notice page"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.create_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notice/create_notice.html')
        self.assertContains(response, 'Create New Notice')

    def test_create_notice_success(self):
        """Test successful notice creation"""
        self.client.force_login(self.admin_user)
        
        data = {
            'title': 'Test Notice Title',
            'content': 'This is a test notice content with enough characters to meet the minimum requirement.',
            'expiry_date': self.future_date.strftime('%Y-%m-%dT%H:%M'),
            'audience': 'ALL',
            'priority': 5
        }
        
        response = self.client.post(self.create_url, data)
        
        self.assertRedirects(response, reverse('notice:notice_list'))
        
        # Check notice was created
        notice = Notice.objects.get(title='Test Notice Title')
        self.assertEqual(notice.content, 'This is a test notice content with enough characters to meet the minimum requirement.')
        self.assertEqual(notice.audience, 'ALL')
        self.assertEqual(notice.created_by, self.admin_user)
        self.assertEqual(notice.priority, 5)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('created successfully', str(messages[0]))

    def test_create_notice_invalid_data(self):
        """Test notice creation with invalid data"""
        self.client.force_login(self.admin_user)
        
        data = {
            'title': 'Hi',  # Too short
            'content': 'Short',  # Too short
            'expiry_date': self.future_date.strftime('%Y-%m-%dT%H:%M'),
            'audience': 'ALL',
            'priority': 5
        }
        
        response = self.client.post(self.create_url, data)
        
        self.assertRedirects(response, self.create_url)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Please correct the errors', str(messages[0]))


class NoticeManageViewTestCase(TestCase):
    """Test cases for notice management views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.manage_url = reverse('notice:manage_notices')
        
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi Description')
        
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            is_staff=True,
            state='VERIFIED'
        )
        
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Regular User',
            state='VERIFIED'
        )
        
        self.notice = Notice.objects.create(
            title='Test Notice',
            content='Test content',
            expiry_date=timezone.now() + timedelta(days=7),
            audience='ALL',
            created_by=self.admin_user,
            priority=5
        )

    def test_manage_notices_requires_leader_or_admin(self):
        """Test that manage notices requires leader or admin access"""
        # Not logged in
        response = self.client.get(self.manage_url)
        self.assertEqual(response.status_code, 302)
        
        # Regular user (not leader or admin)
        self.client.force_login(self.regular_user)
        response = self.client.get(self.manage_url)
        self.assertEqual(response.status_code, 302)  # Redirects for non-leaders/admins

    def test_manage_notices_admin_access(self):
        """Test that admin can access manage notices page"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.manage_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notice/manage_notices.html')
        self.assertContains(response, 'Manage Notices')
        self.assertContains(response, 'Test Notice')

    def test_edit_notice_success(self):
        """Test successful notice editing"""
        self.client.force_login(self.admin_user)
        edit_url = reverse('notice:edit_notice', kwargs={'pk': self.notice.pk})
        
        data = {
            'title': 'Updated Notice Title',
            'content': 'This is an updated notice content with enough characters.',
            'expiry_date': (timezone.now() + timedelta(days=14)).strftime('%Y-%m-%dT%H:%M'),
            'audience': 'ALL',
            'priority': 8
        }
        
        response = self.client.post(edit_url, data)
        
        self.assertRedirects(response, reverse('notice:manage_notices'))
        
        # Check notice was updated
        self.notice.refresh_from_db()
        self.assertEqual(self.notice.title, 'Updated Notice Title')
        self.assertEqual(self.notice.priority, 8)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('updated successfully', str(messages[0]))

    def test_delete_notice_success(self):
        """Test successful notice deletion"""
        self.client.force_login(self.admin_user)
        delete_url = reverse('notice:delete_notice', kwargs={'pk': self.notice.pk})
        
        response = self.client.post(delete_url)
        
        self.assertRedirects(response, reverse('notice:manage_notices'))
        
        # Check notice was deleted
        self.assertFalse(Notice.objects.filter(pk=self.notice.pk).exists())
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('deleted successfully', str(messages[0]))

    def test_expire_notice_success(self):
        """Test successful notice expiration"""
        self.client.force_login(self.admin_user)
        expire_url = reverse('notice:expire_notice', kwargs={'pk': self.notice.pk})
        
        response = self.client.post(expire_url)
        
        self.assertRedirects(response, reverse('notice:manage_notices'))
        
        # Check notice was expired
        self.notice.refresh_from_db()
        self.assertFalse(self.notice.is_active())
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('expired successfully', str(messages[0]))

    def test_notice_engagement_view(self):
        """Test notice engagement view"""
        self.client.force_login(self.admin_user)
        engagement_url = reverse('notice:notice_engagement', kwargs={'pk': self.notice.pk})
        
        # Create some acknowledgments
        user1 = User.objects.create_user(email='user1@example.com', password='pass1', full_name='User 1', state='VERIFIED')
        user2 = User.objects.create_user(email='user2@example.com', password='pass2', full_name='User 2', state='VERIFIED')
        
        NoticeAcknowledgment.objects.create(notice=self.notice, user=user1)
        NoticeAcknowledgment.objects.create(notice=self.notice, user=user2)
        
        response = self.client.get(engagement_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notice/notice_engagement.html')
        self.assertContains(response, 'User 1')
        self.assertContains(response, 'User 2')
