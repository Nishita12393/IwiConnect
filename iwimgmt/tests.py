from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.utils import timezone
from core.models import Iwi, Hapu

User = get_user_model()


class IwiModelTestCase(TestCase):
    """Test cases for Iwi model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            is_staff=True,
            state='VERIFIED'
        )

    def test_iwi_creation(self):
        """Test creating an Iwi"""
        iwi = Iwi.objects.create(
            name='Test Iwi',
            description='This is a test Iwi description.'
        )
        
        self.assertEqual(iwi.name, 'Test Iwi')
        self.assertEqual(iwi.description, 'This is a test Iwi description.')
        self.assertFalse(iwi.is_archived)
        self.assertIsNone(iwi.archived_at)
        self.assertIsNone(iwi.archived_by)

    def test_iwi_string_representation(self):
        """Test the string representation of an Iwi"""
        iwi = Iwi.objects.create(name='Test Iwi Name')
        self.assertEqual(str(iwi), 'Test Iwi Name')

    def test_iwi_archive(self):
        """Test archiving an Iwi"""
        iwi = Iwi.objects.create(name='Test Iwi')
        
        iwi.archive(archived_by=self.admin_user)
        
        self.assertTrue(iwi.is_archived)
        self.assertIsNotNone(iwi.archived_at)
        self.assertEqual(iwi.archived_by, self.admin_user)

    def test_iwi_unarchive(self):
        """Test unarchiving an Iwi"""
        iwi = Iwi.objects.create(name='Test Iwi')
        iwi.archive(archived_by=self.admin_user)
        
        iwi.unarchive()
        
        self.assertFalse(iwi.is_archived)
        self.assertIsNone(iwi.archived_at)
        self.assertIsNone(iwi.archived_by)

    def test_iwi_ordering(self):
        """Test that Iwis are ordered by name"""
        iwi_c = Iwi.objects.create(name='C Iwi')
        iwi_a = Iwi.objects.create(name='A Iwi')
        iwi_b = Iwi.objects.create(name='B Iwi')
        
        iwis = Iwi.objects.all()
        self.assertEqual(iwis[0], iwi_a)
        self.assertEqual(iwis[1], iwi_b)
        self.assertEqual(iwis[2], iwi_c)


class IwiFormTestCase(TestCase):
    """Test cases for IwiForm validation"""
    
    def setUp(self):
        """Set up test data"""
        self.iwi = Iwi.objects.create(name='Existing Iwi', description='Existing description')

    def test_valid_iwi_form(self):
        """Test valid Iwi form data"""
        from .forms import IwiForm
        
        data = {
            'name': 'New Iwi',
            'description': 'This is a new Iwi description.'
        }
        
        form = IwiForm(data)
        self.assertTrue(form.is_valid())

    def test_iwi_form_duplicate_name(self):
        """Test Iwi form with duplicate name"""
        from .forms import IwiForm
        
        data = {
            'name': 'Existing Iwi',  # Duplicate name
            'description': 'Different description'
        }
        
        form = IwiForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_iwi_form_edit_no_duplicate(self):
        """Test Iwi form edit with same name (should be valid)"""
        from .forms import IwiForm
        
        data = {
            'name': 'Existing Iwi',  # Same name as instance
            'description': 'Updated description'
        }
        
        form = IwiForm(data, instance=self.iwi)
        self.assertTrue(form.is_valid())

    def test_iwi_form_edit_duplicate_other_iwi(self):
        """Test Iwi form edit with name of another Iwi (should be invalid)"""
        from .forms import IwiForm
        
        other_iwi = Iwi.objects.create(name='Other Iwi')
        
        data = {
            'name': 'Other Iwi',  # Name of another Iwi
            'description': 'Updated description'
        }
        
        form = IwiForm(data, instance=self.iwi)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_iwi_form_empty_name(self):
        """Test Iwi form with empty name"""
        from .forms import IwiForm
        
        data = {
            'name': '',
            'description': 'Some description'
        }
        
        form = IwiForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_iwi_form_empty_description(self):
        """Test Iwi form with empty description (should be valid)"""
        from .forms import IwiForm
        
        data = {
            'name': 'New Iwi',
            'description': ''
        }
        
        form = IwiForm(data)
        self.assertTrue(form.is_valid())


class IwiArchiveFormTestCase(TestCase):
    """Test cases for IwiArchiveForm"""
    
    def test_valid_archive_form(self):
        """Test valid archive form data"""
        from .forms import IwiArchiveForm
        
        data = {
            'reason': 'This Iwi is no longer active.'
        }
        
        form = IwiArchiveForm(data)
        self.assertTrue(form.is_valid())

    def test_archive_form_empty_reason(self):
        """Test archive form with empty reason (should be valid)"""
        from .forms import IwiArchiveForm
        
        data = {
            'reason': ''
        }
        
        form = IwiArchiveForm(data)
        self.assertTrue(form.is_valid())

    def test_archive_form_long_reason(self):
        """Test archive form with reason too long"""
        from .forms import IwiArchiveForm
        
        data = {
            'reason': 'A' * 501  # 501 characters, exceeds max_length of 500
        }
        
        form = IwiArchiveForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('reason', form.errors)


class IwiListViewTestCase(TestCase):
    """Test cases for Iwi list view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
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
        
        # Create test Iwis
        self.iwi1 = Iwi.objects.create(name='A Iwi', description='First Iwi')
        self.iwi2 = Iwi.objects.create(name='B Iwi', description='Second Iwi')
        self.archived_iwi = Iwi.objects.create(name='C Iwi', description='Archived Iwi')
        self.archived_iwi.archive(archived_by=self.admin_user)

    def test_iwi_list_view_admin_access(self):
        """Test that admin users can access the Iwi list view"""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('iwimgmt:iwi_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'iwimgmt/iwi_list.html')
        self.assertContains(response, 'A Iwi')
        self.assertContains(response, 'B Iwi')
        self.assertNotContains(response, 'C Iwi')  # Archived Iwi not shown by default

    def test_iwi_list_view_show_archived(self):
        """Test showing archived Iwis in the list"""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('iwimgmt:iwi_list'), {'show_archived': 'true'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A Iwi')
        self.assertContains(response, 'B Iwi')
        self.assertContains(response, 'C Iwi')  # Archived Iwi now shown

    def test_iwi_list_view_non_admin_access(self):
        """Test that non-admin users cannot access the Iwi list view"""
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('iwimgmt:iwi_list'))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login for non-admin users

    def test_iwi_list_view_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the Iwi list view"""
        response = self.client.get(reverse('iwimgmt:iwi_list'))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_iwi_list_view_pagination(self):
        """Test pagination in the Iwi list view"""
        # Create more Iwis to test pagination
        for i in range(20):
            Iwi.objects.create(name=f'Iwi {i}', description=f'Description {i}')
        
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('iwimgmt:iwi_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 15)  # Default page size

    def test_iwi_list_view_ordering(self):
        """Test that Iwis are ordered by name"""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('iwimgmt:iwi_list'))
        
        self.assertEqual(response.status_code, 200)
        iwis = response.context['page_obj']
        self.assertEqual(iwis[0].name, 'A Iwi')
        self.assertEqual(iwis[1].name, 'B Iwi')


class IwiDetailViewTestCase(TestCase):
    """Test cases for Iwi detail view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
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
        
        # Create test Iwi with Hapus
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test description')
        self.hapu1 = Hapu.objects.create(name='Hapu 1', iwi=self.iwi)
        self.hapu2 = Hapu.objects.create(name='Hapu 2', iwi=self.iwi)
        
        # Add users to the Iwi
        self.user1 = User.objects.create_user(
            email='member1@example.com',
            password='pass123',
            full_name='Member 1',
            iwi=self.iwi,
            state='VERIFIED'
        )
        self.user2 = User.objects.create_user(
            email='member2@example.com',
            password='pass123',
            full_name='Member 2',
            iwi=self.iwi,
            state='VERIFIED'
        )

    def test_iwi_detail_view_admin_access(self):
        """Test that admin users can access the Iwi detail view"""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('iwimgmt:iwi_detail', args=[self.iwi.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'iwimgmt/iwi_detail.html')
        self.assertContains(response, 'Test Iwi')
        self.assertContains(response, 'Test description')
        self.assertContains(response, '2')  # Number of Hapus
        self.assertContains(response, '2')  # Number of Members

    def test_iwi_detail_view_non_admin_access(self):
        """Test that non-admin users cannot access the Iwi detail view"""
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('iwimgmt:iwi_detail', args=[self.iwi.id]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login for non-admin users

    def test_iwi_detail_view_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the Iwi detail view"""
        response = self.client.get(reverse('iwimgmt:iwi_detail', args=[self.iwi.id]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_iwi_detail_view_nonexistent_iwi(self):
        """Test accessing detail view for non-existent Iwi"""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('iwimgmt:iwi_detail', args=[99999]))
        
        self.assertEqual(response.status_code, 404)

    def test_iwi_detail_view_archived_iwi(self):
        """Test detail view for archived Iwi"""
        self.iwi.archive(archived_by=self.admin_user)
        
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('iwimgmt:iwi_detail', args=[self.iwi.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Archived')
        self.assertContains(response, 'Unarchive Iwi')

    def test_iwi_detail_view_context_data(self):
        """Test that the correct context data is passed to the template"""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('iwimgmt:iwi_detail', args=[self.iwi.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('iwi', response.context)
        self.assertEqual(response.context['iwi'], self.iwi)


class IwiCreateViewTestCase(TestCase):
    """Test cases for Iwi create view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
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

    def test_iwi_create_view_admin_access(self):
        """Test that admin users can access the Iwi create view"""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('iwimgmt:iwi_create'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'iwimgmt/iwi_form.html')
        self.assertContains(response, 'Create New Iwi')
        self.assertContains(response, 'Create Iwi')

    def test_iwi_create_view_non_admin_access(self):
        """Test that non-admin users cannot access the Iwi create view"""
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('iwimgmt:iwi_create'))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_iwi_create_view_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the Iwi create view"""
        response = self.client.get(reverse('iwimgmt:iwi_create'))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_iwi_create_valid_data(self):
        """Test creating an Iwi with valid data"""
        self.client.login(email='admin@example.com', password='adminpass123')
        
        data = {
            'name': 'New Test Iwi',
            'description': 'This is a new test Iwi description.'
        }
        
        response = self.client.post(reverse('iwimgmt:iwi_create'), data)
        
        self.assertEqual(response.status_code, 302)  # Redirects to list
        self.assertRedirects(response, reverse('iwimgmt:iwi_list'))
        
        # Check that the Iwi was created
        iwi = Iwi.objects.get(name='New Test Iwi')
        self.assertEqual(iwi.description, 'This is a new test Iwi description.')
        self.assertFalse(iwi.is_archived)

    def test_iwi_create_invalid_data(self):
        """Test creating an Iwi with invalid data"""
        self.client.login(email='admin@example.com', password='adminpass123')
        
        data = {
            'name': '',  # Empty name
            'description': 'This is a description.'
        }
        
        response = self.client.post(reverse('iwimgmt:iwi_create'), data)
        
        self.assertEqual(response.status_code, 200)  # Stays on form
        self.assertContains(response, 'Please correct the errors below.')

    def test_iwi_create_duplicate_name(self):
        """Test creating an Iwi with duplicate name"""
        # Create an existing Iwi
        Iwi.objects.create(name='Existing Iwi', description='Existing description')
        
        self.client.login(email='admin@example.com', password='adminpass123')
        
        data = {
            'name': 'Existing Iwi',  # Duplicate name
            'description': 'New description.'
        }
        
        response = self.client.post(reverse('iwimgmt:iwi_create'), data)
        
        self.assertEqual(response.status_code, 200)  # Stays on form
        self.assertContains(response, 'Please correct the errors below.')

    def test_iwi_create_success_message(self):
        """Test that success message is shown after creating Iwi"""
        self.client.login(email='admin@example.com', password='adminpass123')
        
        data = {
            'name': 'Success Test Iwi',
            'description': 'Success test description.'
        }
        
        response = self.client.post(reverse('iwimgmt:iwi_create'), data, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('created successfully', str(messages[0]))


class IwiEditViewTestCase(TestCase):
    """Test cases for Iwi edit view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
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
        
        # Create test Iwi
        self.iwi = Iwi.objects.create(
            name='Original Iwi',
            description='Original description'
        )

    def test_iwi_edit_view_admin_access(self):
        """Test that admin users can access the Iwi edit view"""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('iwimgmt:iwi_edit', args=[self.iwi.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'iwimgmt/iwi_form.html')
        self.assertContains(response, 'Edit Iwi: Original Iwi')
        self.assertContains(response, 'Update Iwi')
        self.assertContains(response, 'Original Iwi')
        self.assertContains(response, 'Original description')

    def test_iwi_edit_view_non_admin_access(self):
        """Test that non-admin users cannot access the Iwi edit view"""
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('iwimgmt:iwi_edit', args=[self.iwi.id]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_iwi_edit_view_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the Iwi edit view"""
        response = self.client.get(reverse('iwimgmt:iwi_edit', args=[self.iwi.id]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_iwi_edit_view_nonexistent_iwi(self):
        """Test accessing edit view for non-existent Iwi"""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('iwimgmt:iwi_edit', args=[99999]))
        
        self.assertEqual(response.status_code, 404)

    def test_iwi_edit_valid_data(self):
        """Test editing an Iwi with valid data"""
        self.client.login(email='admin@example.com', password='adminpass123')
        
        data = {
            'name': 'Updated Iwi Name',
            'description': 'Updated description.'
        }
        
        response = self.client.post(reverse('iwimgmt:iwi_edit', args=[self.iwi.id]), data)
        
        self.assertEqual(response.status_code, 302)  # Redirects to list
        self.assertRedirects(response, reverse('iwimgmt:iwi_list'))
        
        # Check that the Iwi was updated
        self.iwi.refresh_from_db()
        self.assertEqual(self.iwi.name, 'Updated Iwi Name')
        self.assertEqual(self.iwi.description, 'Updated description.')

    def test_iwi_edit_invalid_data(self):
        """Test editing an Iwi with invalid data"""
        self.client.login(email='admin@example.com', password='adminpass123')
        
        data = {
            'name': '',  # Empty name
            'description': 'Updated description.'
        }
        
        response = self.client.post(reverse('iwimgmt:iwi_edit', args=[self.iwi.id]), data)
        
        self.assertEqual(response.status_code, 200)  # Stays on form
        self.assertContains(response, 'Please correct the errors below.')

    def test_iwi_edit_duplicate_name(self):
        """Test editing an Iwi with name of another Iwi"""
        # Create another Iwi
        other_iwi = Iwi.objects.create(name='Other Iwi', description='Other description')
        
        self.client.login(email='admin@example.com', password='adminpass123')
        
        data = {
            'name': 'Other Iwi',  # Name of another Iwi
            'description': 'Updated description.'
        }
        
        response = self.client.post(reverse('iwimgmt:iwi_edit', args=[self.iwi.id]), data)
        
        self.assertEqual(response.status_code, 200)  # Stays on form
        self.assertContains(response, 'Please correct the errors below.')

    def test_iwi_edit_same_name(self):
        """Test editing an Iwi with the same name (should be valid)"""
        self.client.login(email='admin@example.com', password='adminpass123')
        
        data = {
            'name': 'Original Iwi',  # Same name
            'description': 'Updated description.'
        }
        
        response = self.client.post(reverse('iwimgmt:iwi_edit', args=[self.iwi.id]), data)
        
        self.assertEqual(response.status_code, 302)  # Redirects to list
        self.assertRedirects(response, reverse('iwimgmt:iwi_list'))

    def test_iwi_edit_success_message(self):
        """Test that success message is shown after editing Iwi"""
        self.client.login(email='admin@example.com', password='adminpass123')
        
        data = {
            'name': 'Success Edit Iwi',
            'description': 'Success edit description.'
        }
        
        response = self.client.post(reverse('iwimgmt:iwi_edit', args=[self.iwi.id]), data, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('updated successfully', str(messages[0]))


class IwiArchiveViewTestCase(TestCase):
    """Test cases for Iwi archive view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
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
        
        # Create test Iwi
        self.iwi = Iwi.objects.create(
            name='Test Iwi',
            description='Test description'
        )

    def test_iwi_archive_view_admin_access(self):
        """Test that admin users can access the Iwi archive view"""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('iwimgmt:iwi_archive', args=[self.iwi.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'iwimgmt/iwi_archive.html')
        self.assertContains(response, 'Archive Iwi')
        self.assertContains(response, 'Test Iwi')

    def test_iwi_archive_view_non_admin_access(self):
        """Test that non-admin users cannot access the Iwi archive view"""
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('iwimgmt:iwi_archive', args=[self.iwi.id]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_iwi_archive_view_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the Iwi archive view"""
        response = self.client.get(reverse('iwimgmt:iwi_archive', args=[self.iwi.id]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_iwi_archive_view_nonexistent_iwi(self):
        """Test accessing archive view for non-existent Iwi"""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('iwimgmt:iwi_archive', args=[99999]))
        
        self.assertEqual(response.status_code, 404)

    def test_iwi_archive_view_already_archived_iwi(self):
        """Test accessing archive view for already archived Iwi"""
        self.iwi.archive(archived_by=self.admin_user)
        
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('iwimgmt:iwi_archive', args=[self.iwi.id]))
        
        self.assertEqual(response.status_code, 404)

    def test_iwi_archive_valid_data(self):
        """Test archiving an Iwi with valid data"""
        self.client.login(email='admin@example.com', password='adminpass123')
        
        data = {
            'reason': 'This Iwi is no longer active.'
        }
        
        response = self.client.post(reverse('iwimgmt:iwi_archive', args=[self.iwi.id]), data)
        
        self.assertEqual(response.status_code, 302)  # Redirects to list
        self.assertRedirects(response, reverse('iwimgmt:iwi_list'))
        
        # Check that the Iwi was archived
        self.iwi.refresh_from_db()
        self.assertTrue(self.iwi.is_archived)
        self.assertIsNotNone(self.iwi.archived_at)
        self.assertEqual(self.iwi.archived_by, self.admin_user)

    def test_iwi_archive_empty_reason(self):
        """Test archiving an Iwi with empty reason"""
        self.client.login(email='admin@example.com', password='adminpass123')
        
        data = {
            'reason': ''
        }
        
        response = self.client.post(reverse('iwimgmt:iwi_archive', args=[self.iwi.id]), data)
        
        self.assertEqual(response.status_code, 302)  # Redirects to list
        self.assertRedirects(response, reverse('iwimgmt:iwi_list'))
        
        # Check that the Iwi was archived
        self.iwi.refresh_from_db()
        self.assertTrue(self.iwi.is_archived)

    def test_iwi_archive_success_message(self):
        """Test that success message is shown after archiving Iwi"""
        self.client.login(email='admin@example.com', password='adminpass123')
        
        data = {
            'reason': 'Archive reason.'
        }
        
        response = self.client.post(reverse('iwimgmt:iwi_archive', args=[self.iwi.id]), data, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('has been archived', str(messages[0]))


class IwiUnarchiveViewTestCase(TestCase):
    """Test cases for Iwi unarchive view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
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
        
        # Create test Iwi and archive it
        self.iwi = Iwi.objects.create(
            name='Test Iwi',
            description='Test description'
        )
        self.iwi.archive(archived_by=self.admin_user)

    def test_iwi_unarchive_view_admin_access(self):
        """Test that admin users can access the Iwi unarchive view"""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('iwimgmt:iwi_unarchive', args=[self.iwi.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'iwimgmt/iwi_unarchive.html')
        self.assertContains(response, 'Unarchive Iwi')
        self.assertContains(response, 'Test Iwi')

    def test_iwi_unarchive_view_non_admin_access(self):
        """Test that non-admin users cannot access the Iwi unarchive view"""
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('iwimgmt:iwi_unarchive', args=[self.iwi.id]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_iwi_unarchive_view_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the Iwi unarchive view"""
        response = self.client.get(reverse('iwimgmt:iwi_unarchive', args=[self.iwi.id]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_iwi_unarchive_view_nonexistent_iwi(self):
        """Test accessing unarchive view for non-existent Iwi"""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('iwimgmt:iwi_unarchive', args=[99999]))
        
        self.assertEqual(response.status_code, 404)

    def test_iwi_unarchive_view_active_iwi(self):
        """Test accessing unarchive view for active (non-archived) Iwi"""
        # Create an active Iwi
        active_iwi = Iwi.objects.create(name='Active Iwi', description='Active description')
        
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('iwimgmt:iwi_unarchive', args=[active_iwi.id]))
        
        self.assertEqual(response.status_code, 404)

    def test_iwi_unarchive_success(self):
        """Test unarchiving an Iwi"""
        self.client.login(email='admin@example.com', password='adminpass123')
        
        response = self.client.post(reverse('iwimgmt:iwi_unarchive', args=[self.iwi.id]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to list
        self.assertRedirects(response, reverse('iwimgmt:iwi_list'))
        
        # Check that the Iwi was unarchived
        self.iwi.refresh_from_db()
        self.assertFalse(self.iwi.is_archived)
        self.assertIsNone(self.iwi.archived_at)
        self.assertIsNone(self.iwi.archived_by)

    def test_iwi_unarchive_success_message(self):
        """Test that success message is shown after unarchiving Iwi"""
        self.client.login(email='admin@example.com', password='adminpass123')
        
        response = self.client.post(reverse('iwimgmt:iwi_unarchive', args=[self.iwi.id]), follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('has been unarchived', str(messages[0]))


class IwiManagementIntegrationTestCase(TestCase):
    """Integration test cases for Iwi management workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            is_staff=True,
            state='VERIFIED'
        )

    def test_complete_iwi_lifecycle(self):
        """Test complete Iwi lifecycle: create, edit, archive, unarchive"""
        self.client.login(email='admin@example.com', password='adminpass123')
        
        # 1. Create Iwi
        create_data = {
            'name': 'Lifecycle Test Iwi',
            'description': 'Initial description'
        }
        response = self.client.post(reverse('iwimgmt:iwi_create'), create_data)
        self.assertEqual(response.status_code, 302)
        
        iwi = Iwi.objects.get(name='Lifecycle Test Iwi')
        self.assertFalse(iwi.is_archived)
        
        # 2. Edit Iwi
        edit_data = {
            'name': 'Lifecycle Test Iwi',
            'description': 'Updated description'
        }
        response = self.client.post(reverse('iwimgmt:iwi_edit', args=[iwi.id]), edit_data)
        self.assertEqual(response.status_code, 302)
        
        iwi.refresh_from_db()
        self.assertEqual(iwi.description, 'Updated description')
        
        # 3. Archive Iwi
        archive_data = {
            'reason': 'Testing archive functionality'
        }
        response = self.client.post(reverse('iwimgmt:iwi_archive', args=[iwi.id]), archive_data)
        self.assertEqual(response.status_code, 302)
        
        iwi.refresh_from_db()
        self.assertTrue(iwi.is_archived)
        self.assertEqual(iwi.archived_by, self.admin_user)
        
        # 4. Unarchive Iwi
        response = self.client.post(reverse('iwimgmt:iwi_unarchive', args=[iwi.id]))
        self.assertEqual(response.status_code, 302)
        
        iwi.refresh_from_db()
        self.assertFalse(iwi.is_archived)
        self.assertIsNone(iwi.archived_at)
        self.assertIsNone(iwi.archived_by)

    def test_iwi_list_filtering(self):
        """Test Iwi list filtering with archived and active Iwis"""
        # Create active and archived Iwis
        active_iwi = Iwi.objects.create(name='Active Iwi', description='Active')
        archived_iwi = Iwi.objects.create(name='Archived Iwi', description='Archived')
        archived_iwi.archive(archived_by=self.admin_user)
        
        # Verify the archived Iwi is actually archived
        archived_iwi.refresh_from_db()
        self.assertTrue(archived_iwi.is_archived)
        
        self.client.login(email='admin@example.com', password='adminpass123')
        
        # Test default view (active only)
        response = self.client.get(reverse('iwimgmt:iwi_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Active Iwi')
        # Check that archived Iwi is not in the table body
        self.assertNotContains(response, '<strong>Archived Iwi</strong>')
        
        # Test showing archived
        response = self.client.get(reverse('iwimgmt:iwi_list'), {'show_archived': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Active Iwi')
        self.assertContains(response, 'Archived Iwi')
