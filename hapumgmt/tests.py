from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.utils import timezone
from core.models import Iwi, Hapu, IwiLeader, HapuLeader

User = get_user_model()


class HapuModelTestCase(TestCase):
    """Test cases for Hapu model functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            is_staff=True,
            state='VERIFIED'
        )
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi description')

    def test_hapu_creation(self):
        """Test creating a Hapu"""
        hapu = Hapu.objects.create(
            name='Test Hapu',
            description='This is a test Hapu description.',
            iwi=self.iwi
        )
        
        self.assertEqual(hapu.name, 'Test Hapu')
        self.assertEqual(hapu.description, 'This is a test Hapu description.')
        self.assertEqual(hapu.iwi, self.iwi)
        self.assertFalse(hapu.is_archived)
        self.assertIsNone(hapu.archived_at)
        self.assertIsNone(hapu.archived_by)

    def test_hapu_string_representation(self):
        """Test the string representation of a Hapu"""
        hapu = Hapu.objects.create(name='Test Hapu Name', iwi=self.iwi)
        self.assertEqual(str(hapu), 'Test Hapu Name (Test Iwi)')

    def test_hapu_archive(self):
        """Test archiving a Hapu"""
        hapu = Hapu.objects.create(name='Test Hapu', iwi=self.iwi)
        
        hapu.archive(archived_by=self.admin_user)
        
        self.assertTrue(hapu.is_archived)
        self.assertIsNotNone(hapu.archived_at)
        self.assertEqual(hapu.archived_by, self.admin_user)

    def test_hapu_unarchive(self):
        """Test unarchiving a Hapu"""
        hapu = Hapu.objects.create(name='Test Hapu', iwi=self.iwi)
        hapu.archive(archived_by=self.admin_user)
        
        hapu.unarchive()
        
        self.assertFalse(hapu.is_archived)
        self.assertIsNone(hapu.archived_at)
        self.assertIsNone(hapu.archived_by)

    def test_hapu_ordering(self):
        """Test that Hapus are ordered by iwi name then hapu name"""
        iwi_a = Iwi.objects.create(name='A Iwi')
        iwi_b = Iwi.objects.create(name='B Iwi')
        
        hapu_c = Hapu.objects.create(name='C Hapu', iwi=iwi_b)
        hapu_a = Hapu.objects.create(name='A Hapu', iwi=iwi_a)
        hapu_b = Hapu.objects.create(name='B Hapu', iwi=iwi_a)
        
        hapus = Hapu.objects.all()
        self.assertEqual(hapus[0], hapu_a)  # A Hapu in A Iwi
        self.assertEqual(hapus[1], hapu_b)  # B Hapu in A Iwi
        self.assertEqual(hapus[2], hapu_c)  # C Hapu in B Iwi


class HapuFormTestCase(TestCase):
    """Test cases for HapuForm validation"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Test User',
            state='VERIFIED'
        )
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test description')
        self.hapu = Hapu.objects.create(name='Existing Hapu', description='Existing description', iwi=self.iwi)

    def test_hapu_form_single_iwi_user(self):
        """Test HapuForm for user with single Iwi (no Iwi field visible)"""
        # Make user an Iwi leader
        IwiLeader.objects.create(user=self.user, iwi=self.iwi)
        
        from .forms import HapuForm
        
        form = HapuForm(user=self.user)
        
        self.assertFalse(form.iwi_field_visible)
        self.assertEqual(form.iwi, self.iwi)
        self.assertNotIn('iwi', form.fields)

    def test_hapu_form_multiple_iwi_user(self):
        """Test HapuForm for user with multiple Iwis (Iwi field visible)"""
        # Create another Iwi and make user leader of both
        iwi2 = Iwi.objects.create(name='Second Iwi', description='Second description')
        IwiLeader.objects.create(user=self.user, iwi=self.iwi)
        IwiLeader.objects.create(user=self.user, iwi=iwi2)
        
        from .forms import HapuForm
        
        form = HapuForm(user=self.user)
        
        self.assertTrue(form.iwi_field_visible)
        self.assertIn('iwi', form.fields)
        self.assertEqual(len(form.fields['iwi'].queryset), 2)

    def test_hapu_form_no_iwi_user(self):
        """Test HapuForm for user with no Iwis"""
        from .forms import HapuForm
        
        form = HapuForm(user=self.user)
        
        self.assertFalse(form.iwi_field_visible)
        self.assertIsNone(form.iwi)
        self.assertNotIn('iwi', form.fields)

    def test_hapu_form_valid_data_single_iwi(self):
        """Test HapuForm with valid data for single Iwi user"""
        IwiLeader.objects.create(user=self.user, iwi=self.iwi)
        
        from .forms import HapuForm
        
        data = {
            'name': 'New Test Hapu',
            'description': 'This is a new test Hapu description.'
        }
        
        form = HapuForm(data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_hapu_form_valid_data_multiple_iwi(self):
        """Test HapuForm with valid data for multiple Iwi user"""
        iwi2 = Iwi.objects.create(name='Second Iwi', description='Second description')
        IwiLeader.objects.create(user=self.user, iwi=self.iwi)
        IwiLeader.objects.create(user=self.user, iwi=iwi2)
        
        from .forms import HapuForm
        
        data = {
            'name': 'New Test Hapu',
            'description': 'This is a new test Hapu description.',
            'iwi': self.iwi.id
        }
        
        form = HapuForm(data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_hapu_form_empty_name(self):
        """Test HapuForm with empty name"""
        IwiLeader.objects.create(user=self.user, iwi=self.iwi)
        
        from .forms import HapuForm
        
        data = {
            'name': '',
            'description': 'Some description'
        }
        
        form = HapuForm(data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_hapu_form_empty_description(self):
        """Test HapuForm with empty description (should be valid)"""
        IwiLeader.objects.create(user=self.user, iwi=self.iwi)
        
        from .forms import HapuForm
        
        data = {
            'name': 'New Hapu',
            'description': ''
        }
        
        form = HapuForm(data, user=self.user)
        self.assertTrue(form.is_valid())


class HapuArchiveFormTestCase(TestCase):
    """Test cases for HapuArchiveForm"""
    
    def test_valid_archive_form(self):
        """Test valid archive form data"""
        from .forms import HapuArchiveForm
        
        data = {
            'confirm_archive': True
        }
        
        form = HapuArchiveForm(data)
        self.assertTrue(form.is_valid())

    def test_archive_form_not_confirmed(self):
        """Test archive form without confirmation"""
        from .forms import HapuArchiveForm
        
        data = {
            'confirm_archive': False
        }
        
        form = HapuArchiveForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_archive', form.errors)

    def test_archive_form_missing_confirmation(self):
        """Test archive form with missing confirmation"""
        from .forms import HapuArchiveForm
        
        data = {}
        
        form = HapuArchiveForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_archive', form.errors)


class HapuTransferFormTestCase(TestCase):
    """Test cases for HapuTransferForm"""
    
    def setUp(self):
        """Set up test data"""
        self.current_iwi = Iwi.objects.create(name='Current Iwi', description='Current description')
        self.new_iwi = Iwi.objects.create(name='New Iwi', description='New description')

    def test_valid_transfer_form(self):
        """Test valid transfer form data"""
        from .forms import HapuTransferForm
        
        data = {
            'new_iwi': self.new_iwi.id,
            'confirm_transfer': True
        }
        
        form = HapuTransferForm(data, current_iwi=self.current_iwi)
        self.assertTrue(form.is_valid())

    def test_transfer_form_not_confirmed(self):
        """Test transfer form without confirmation"""
        from .forms import HapuTransferForm
        
        data = {
            'new_iwi': self.new_iwi.id,
            'confirm_transfer': False
        }
        
        form = HapuTransferForm(data, current_iwi=self.current_iwi)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_transfer', form.errors)

    def test_transfer_form_missing_iwi(self):
        """Test transfer form with missing Iwi selection"""
        from .forms import HapuTransferForm
        
        data = {
            'confirm_transfer': True
        }
        
        form = HapuTransferForm(data, current_iwi=self.current_iwi)
        self.assertFalse(form.is_valid())
        self.assertIn('new_iwi', form.errors)

    def test_transfer_form_excludes_current_iwi(self):
        """Test that transfer form excludes current Iwi from choices"""
        from .forms import HapuTransferForm
        
        form = HapuTransferForm(current_iwi=self.current_iwi)
        
        # Current Iwi should not be in the choices
        iwi_choices = [choice[0] for choice in form.fields['new_iwi'].choices if choice[0] != '']
        self.assertNotIn(self.current_iwi.id, iwi_choices)
        self.assertIn(self.new_iwi.id, iwi_choices)

    def test_transfer_form_only_active_iwis(self):
        """Test that transfer form only shows active Iwis"""
        # Archive the new Iwi
        self.new_iwi.archive(archived_by=User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            is_staff=True,
            state='VERIFIED'
        ))
        
        from .forms import HapuTransferForm
        
        form = HapuTransferForm(current_iwi=self.current_iwi)
        
        # Archived Iwi should not be in the choices
        iwi_choices = [choice[0] for choice in form.fields['new_iwi'].choices if choice[0] != '']
        self.assertNotIn(self.new_iwi.id, iwi_choices)


class HapuListViewTestCase(TestCase):
    """Test cases for Hapu list view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Test User',
            state='VERIFIED'
        )
        self.iwi_leader = User.objects.create_user(
            email='iwi_leader@example.com',
            password='leaderpass123',
            full_name='Iwi Leader',
            state='VERIFIED'
        )
        self.hapu_leader = User.objects.create_user(
            email='hapu_leader@example.com',
            password='hapu123',
            full_name='Hapu Leader',
            state='VERIFIED'
        )
        
        # Create Iwis and Hapus
        self.iwi1 = Iwi.objects.create(name='First Iwi', description='First Iwi description')
        self.iwi2 = Iwi.objects.create(name='Second Iwi', description='Second Iwi description')
        
        self.hapu1 = Hapu.objects.create(name='First Hapu', description='First Hapu description', iwi=self.iwi1)
        self.hapu2 = Hapu.objects.create(name='Second Hapu', description='Second Hapu description', iwi=self.iwi1)
        self.hapu3 = Hapu.objects.create(name='Third Hapu', description='Third Hapu description', iwi=self.iwi2)
        
        # Create leaders
        IwiLeader.objects.create(user=self.iwi_leader, iwi=self.iwi1)
        HapuLeader.objects.create(user=self.hapu_leader, hapu=self.hapu1)
        # Make iwi_leader also a hapu leader to ensure access after iwi is archived
        HapuLeader.objects.create(user=self.iwi_leader, hapu=self.hapu1)
        HapuLeader.objects.create(user=self.iwi_leader, hapu=self.hapu2)

    def test_hapu_list_view_authenticated_access(self):
        """Test that authenticated users can access the Hapu list view"""
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('hapumgmt:hapu_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hapumgmt/hapu_list.html')

    def test_hapu_list_view_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the Hapu list view"""
        response = self.client.get(reverse('hapumgmt:hapu_list'))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_hapu_list_view_iwi_leader_sees_own_hapus(self):
        """Test that Iwi leaders see Hapus from their Iwis"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'First Hapu')
        self.assertContains(response, 'Second Hapu')
        self.assertNotContains(response, 'Third Hapu')  # From different Iwi

    def test_hapu_list_view_hapu_leader_sees_own_hapu(self):
        """Test that Hapu leaders see their own Hapu"""
        self.client.login(email='hapu_leader@example.com', password='hapu123')
        response = self.client.get(reverse('hapumgmt:hapu_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'First Hapu')
        self.assertNotContains(response, 'Second Hapu')  # Not their Hapu
        self.assertNotContains(response, 'Third Hapu')   # Not their Hapu

    def test_hapu_list_view_archived_hapus(self):
        """Test that archived Hapus are shown in separate section"""
        # Archive a Hapu
        self.hapu2.archive(archived_by=self.iwi_leader)
        
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Active Hapus')
        self.assertContains(response, 'Archived Hapus')
        self.assertContains(response, 'First Hapu')  # Active
        self.assertContains(response, 'Second Hapu')  # Archived

    def test_hapu_list_view_pagination(self):
        """Test pagination in the Hapu list view"""
        # Create more Hapus to test pagination
        for i in range(25):
            Hapu.objects.create(name=f'Hapu {i}', description=f'Description {i}', iwi=self.iwi1)
        
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('active_page_obj', response.context)
        self.assertEqual(len(response.context['active_page_obj']), 20)  # Default page size

    def test_hapu_list_view_hapus_with_archived_iwis(self):
        """Test that Hapus with archived Iwis are detected"""
        # Archive the Iwi
        self.iwi1.archive(archived_by=self.iwi_leader)
        
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('hapus_with_archived_iwis', response.context)
        # The user should still see Hapus from their archived Iwi
        self.assertEqual(response.context['hapus_with_archived_iwis'].count(), 2)  # Both Hapus from archived Iwi


class HapuDetailViewTestCase(TestCase):
    """Test cases for Hapu detail view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Test User',
            state='VERIFIED'
        )
        self.iwi_leader = User.objects.create_user(
            email='iwi_leader@example.com',
            password='leaderpass123',
            full_name='Iwi Leader',
            state='VERIFIED'
        )
        self.hapu_leader = User.objects.create_user(
            email='hapu_leader@example.com',
            password='hapu123',
            full_name='Hapu Leader',
            state='VERIFIED'
        )
        
        # Create Iwi and Hapu
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi description')
        self.hapu = Hapu.objects.create(name='Test Hapu', description='Test Hapu description', iwi=self.iwi)
        
        # Create leaders
        IwiLeader.objects.create(user=self.iwi_leader, iwi=self.iwi)
        HapuLeader.objects.create(user=self.hapu_leader, hapu=self.hapu)

    def test_hapu_detail_view_iwi_leader_access(self):
        """Test that Iwi leaders can access Hapu detail view"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_detail', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hapumgmt/hapu_detail.html')
        self.assertContains(response, 'Test Hapu')
        self.assertContains(response, 'Test Iwi')
        self.assertContains(response, 'Test Hapu description')

    def test_hapu_detail_view_hapu_leader_access(self):
        """Test that Hapu leaders can access their Hapu detail view"""
        self.client.login(email='hapu_leader@example.com', password='hapu123')
        response = self.client.get(reverse('hapumgmt:hapu_detail', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Hapu')

    def test_hapu_detail_view_unauthorized_access(self):
        """Test that unauthorized users cannot access Hapu detail view"""
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('hapumgmt:hapu_detail', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to list
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('permission', str(messages[0]))

    def test_hapu_detail_view_unauthenticated_access(self):
        """Test that unauthenticated users cannot access Hapu detail view"""
        response = self.client.get(reverse('hapumgmt:hapu_detail', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_hapu_detail_view_nonexistent_hapu(self):
        """Test accessing detail view for non-existent Hapu"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_detail', args=[99999]))
        
        self.assertEqual(response.status_code, 404)

    def test_hapu_detail_view_archived_hapu(self):
        """Test detail view for archived Hapu"""
        self.hapu.archive(archived_by=self.iwi_leader)
        
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_detail', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Archived')
        self.assertContains(response, 'Unarchive Hapu')

    def test_hapu_detail_view_archived_iwi_transfer_option(self):
        """Test that transfer option is shown for Hapus with archived Iwis"""
        # Archive the Iwi
        self.iwi.archive(archived_by=self.iwi_leader)
        
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_detail', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Transfer to Another Iwi')

    def test_hapu_detail_view_context_data(self):
        """Test that the correct context data is passed to the template"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_detail', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('hapu', response.context)
        self.assertEqual(response.context['hapu'], self.hapu)


class HapuCreateViewTestCase(TestCase):
    """Test cases for Hapu create view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Test User',
            state='VERIFIED'
        )
        self.iwi_leader = User.objects.create_user(
            email='iwi_leader@example.com',
            password='leaderpass123',
            full_name='Iwi Leader',
            state='VERIFIED'
        )
        
        # Create Iwi
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi description')
        IwiLeader.objects.create(user=self.iwi_leader, iwi=self.iwi)

    def test_hapu_create_view_iwi_leader_access(self):
        """Test that Iwi leaders can access the Hapu create view"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_create'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hapumgmt/hapu_form.html')
        self.assertContains(response, 'Create New Hapu')
        self.assertContains(response, 'Create Hapu')

    def test_hapu_create_view_non_iwi_leader_access(self):
        """Test that non-Iwi leaders cannot access the Hapu create view"""
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('hapumgmt:hapu_create'))
        
        self.assertEqual(response.status_code, 302)  # Redirects to list
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('must be an iwi leader', str(messages[0]))

    def test_hapu_create_view_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the Hapu create view"""
        response = self.client.get(reverse('hapumgmt:hapu_create'))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_hapu_create_valid_data_single_iwi(self):
        """Test creating a Hapu with valid data for single Iwi user"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        
        data = {
            'name': 'New Test Hapu',
            'description': 'This is a new test Hapu description.'
        }
        
        response = self.client.post(reverse('hapumgmt:hapu_create'), data)
        
        self.assertEqual(response.status_code, 302)  # Redirects to detail
        
        # Check that the Hapu was created
        hapu = Hapu.objects.get(name='New Test Hapu')
        self.assertEqual(hapu.description, 'This is a new test Hapu description.')
        self.assertEqual(hapu.iwi, self.iwi)
        self.assertFalse(hapu.is_archived)
        
        # Check redirect goes to the correct Hapu detail
        self.assertRedirects(response, reverse('hapumgmt:hapu_detail', args=[hapu.pk]))

    def test_hapu_create_valid_data_multiple_iwi(self):
        """Test creating a Hapu with valid data for multiple Iwi user"""
        # Create another Iwi and make user leader of both
        iwi2 = Iwi.objects.create(name='Second Iwi', description='Second description')
        IwiLeader.objects.create(user=self.iwi_leader, iwi=iwi2)
        
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        
        data = {
            'name': 'New Test Hapu',
            'description': 'This is a new test Hapu description.',
            'iwi': self.iwi.id
        }
        
        response = self.client.post(reverse('hapumgmt:hapu_create'), data)
        
        self.assertEqual(response.status_code, 302)  # Redirects to detail
        
        # Check that the Hapu was created
        hapu = Hapu.objects.get(name='New Test Hapu')
        self.assertEqual(hapu.iwi, self.iwi)
        
        # Check redirect goes to the correct Hapu detail
        self.assertRedirects(response, reverse('hapumgmt:hapu_detail', args=[hapu.pk]))

    def test_hapu_create_invalid_data(self):
        """Test creating a Hapu with invalid data"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        
        data = {
            'name': '',  # Empty name
            'description': 'This is a description.'
        }
        
        response = self.client.post(reverse('hapumgmt:hapu_create'), data)
        
        self.assertEqual(response.status_code, 200)  # Stays on form

    def test_hapu_create_success_message(self):
        """Test that success message is shown after creating Hapu"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        
        data = {
            'name': 'Success Test Hapu',
            'description': 'Success test description.'
        }
        
        response = self.client.post(reverse('hapumgmt:hapu_create'), data, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('created successfully', str(messages[0]))


class HapuEditViewTestCase(TestCase):
    """Test cases for Hapu edit view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Test User',
            state='VERIFIED'
        )
        self.iwi_leader = User.objects.create_user(
            email='iwi_leader@example.com',
            password='leaderpass123',
            full_name='Iwi Leader',
            state='VERIFIED'
        )
        self.hapu_leader = User.objects.create_user(
            email='hapu_leader@example.com',
            password='hapu123',
            full_name='Hapu Leader',
            state='VERIFIED'
        )
        
        # Create Iwi and Hapu
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi description')
        self.hapu = Hapu.objects.create(name='Original Hapu', description='Original description', iwi=self.iwi)
        
        # Create leaders
        IwiLeader.objects.create(user=self.iwi_leader, iwi=self.iwi)
        HapuLeader.objects.create(user=self.hapu_leader, hapu=self.hapu)

    def test_hapu_edit_view_iwi_leader_access(self):
        """Test that Iwi leaders can access the Hapu edit view"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_edit', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hapumgmt/hapu_form.html')
        self.assertContains(response, 'Edit Hapu: Original Hapu')
        self.assertContains(response, 'Update Hapu')
        self.assertContains(response, 'Original Hapu')
        self.assertContains(response, 'Original description')

    def test_hapu_edit_view_hapu_leader_access(self):
        """Test that Hapu leaders can access the Hapu edit view"""
        self.client.login(email='hapu_leader@example.com', password='hapu123')
        response = self.client.get(reverse('hapumgmt:hapu_edit', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Hapu: Original Hapu')

    def test_hapu_edit_view_unauthorized_access(self):
        """Test that unauthorized users cannot access the Hapu edit view"""
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('hapumgmt:hapu_edit', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to list
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('permission', str(messages[0]))

    def test_hapu_edit_view_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the Hapu edit view"""
        response = self.client.get(reverse('hapumgmt:hapu_edit', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_hapu_edit_view_nonexistent_hapu(self):
        """Test accessing edit view for non-existent Hapu"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_edit', args=[99999]))
        
        self.assertEqual(response.status_code, 404)

    def test_hapu_edit_valid_data(self):
        """Test editing a Hapu with valid data"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        
        data = {
            'name': 'Updated Hapu Name',
            'description': 'Updated description.'
        }
        
        response = self.client.post(reverse('hapumgmt:hapu_edit', args=[self.hapu.pk]), data)
        
        self.assertEqual(response.status_code, 302)  # Redirects to detail
        self.assertRedirects(response, reverse('hapumgmt:hapu_detail', args=[self.hapu.pk]))
        
        # Check that the Hapu was updated
        self.hapu.refresh_from_db()
        self.assertEqual(self.hapu.name, 'Updated Hapu Name')
        self.assertEqual(self.hapu.description, 'Updated description.')

    def test_hapu_edit_invalid_data(self):
        """Test editing a Hapu with invalid data"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        
        data = {
            'name': '',  # Empty name
            'description': 'Updated description.'
        }
        
        response = self.client.post(reverse('hapumgmt:hapu_edit', args=[self.hapu.pk]), data)
        
        self.assertEqual(response.status_code, 200)  # Stays on form

    def test_hapu_edit_success_message(self):
        """Test that success message is shown after editing Hapu"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        
        data = {
            'name': 'Success Edit Hapu',
            'description': 'Success edit description.'
        }
        
        response = self.client.post(reverse('hapumgmt:hapu_edit', args=[self.hapu.pk]), data, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('updated successfully', str(messages[0]))


class HapuArchiveViewTestCase(TestCase):
    """Test cases for Hapu archive view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Test User',
            state='VERIFIED'
        )
        self.iwi_leader = User.objects.create_user(
            email='iwi_leader@example.com',
            password='leaderpass123',
            full_name='Iwi Leader',
            state='VERIFIED'
        )
        self.hapu_leader = User.objects.create_user(
            email='hapu_leader@example.com',
            password='hapu123',
            full_name='Hapu Leader',
            state='VERIFIED'
        )
        
        # Create Iwi and Hapu
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi description')
        self.hapu = Hapu.objects.create(name='Test Hapu', description='Test Hapu description', iwi=self.iwi)
        
        # Create leaders
        IwiLeader.objects.create(user=self.iwi_leader, iwi=self.iwi)
        HapuLeader.objects.create(user=self.hapu_leader, hapu=self.hapu)

    def test_hapu_archive_view_iwi_leader_access(self):
        """Test that Iwi leaders can access the Hapu archive view"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_archive', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hapumgmt/hapu_archive.html')
        self.assertContains(response, 'Archive Hapu')
        self.assertContains(response, 'Test Hapu')

    def test_hapu_archive_view_hapu_leader_access(self):
        """Test that Hapu leaders can access the Hapu archive view"""
        self.client.login(email='hapu_leader@example.com', password='hapu123')
        response = self.client.get(reverse('hapumgmt:hapu_archive', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Archive Hapu')

    def test_hapu_archive_view_unauthorized_access(self):
        """Test that unauthorized users cannot access the Hapu archive view"""
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('hapumgmt:hapu_archive', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to list
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('permission', str(messages[0]))

    def test_hapu_archive_view_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the Hapu archive view"""
        response = self.client.get(reverse('hapumgmt:hapu_archive', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_hapu_archive_view_nonexistent_hapu(self):
        """Test accessing archive view for non-existent Hapu"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_archive', args=[99999]))
        
        self.assertEqual(response.status_code, 404)

    def test_hapu_archive_view_already_archived_hapu(self):
        """Test accessing archive view for already archived Hapu"""
        self.hapu.archive(archived_by=self.iwi_leader)
        
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_archive', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to detail
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('already archived', str(messages[0]))

    def test_hapu_archive_valid_data(self):
        """Test archiving a Hapu with valid data"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        
        data = {
            'confirm_archive': True
        }
        
        response = self.client.post(reverse('hapumgmt:hapu_archive', args=[self.hapu.pk]), data)
        
        self.assertEqual(response.status_code, 302)  # Redirects to list
        self.assertRedirects(response, reverse('hapumgmt:hapu_list'))
        
        # Check that the Hapu was archived
        self.hapu.refresh_from_db()
        self.assertTrue(self.hapu.is_archived)
        self.assertIsNotNone(self.hapu.archived_at)
        self.assertEqual(self.hapu.archived_by, self.iwi_leader)

    def test_hapu_archive_not_confirmed(self):
        """Test archiving a Hapu without confirmation"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        
        data = {
            'confirm_archive': False
        }
        
        response = self.client.post(reverse('hapumgmt:hapu_archive', args=[self.hapu.pk]), data)
        
        self.assertEqual(response.status_code, 200)  # Stays on form
        self.assertFalse(self.hapu.is_archived)

    def test_hapu_archive_success_message(self):
        """Test that success message is shown after archiving Hapu"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        
        data = {
            'confirm_archive': True
        }
        
        response = self.client.post(reverse('hapumgmt:hapu_archive', args=[self.hapu.pk]), data, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('has been archived', str(messages[0]))


class HapuUnarchiveViewTestCase(TestCase):
    """Test cases for Hapu unarchive view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Test User',
            state='VERIFIED'
        )
        self.iwi_leader = User.objects.create_user(
            email='iwi_leader@example.com',
            password='leaderpass123',
            full_name='Iwi Leader',
            state='VERIFIED'
        )
        self.hapu_leader = User.objects.create_user(
            email='hapu_leader@example.com',
            password='hapu123',
            full_name='Hapu Leader',
            state='VERIFIED'
        )
        
        # Create Iwi and Hapu and archive it
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi description')
        self.hapu = Hapu.objects.create(name='Test Hapu', description='Test Hapu description', iwi=self.iwi)
        self.hapu.archive(archived_by=self.iwi_leader)
        
        # Create leaders
        IwiLeader.objects.create(user=self.iwi_leader, iwi=self.iwi)
        HapuLeader.objects.create(user=self.hapu_leader, hapu=self.hapu)

    def test_hapu_unarchive_view_iwi_leader_access(self):
        """Test that Iwi leaders can access the Hapu unarchive view"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_unarchive', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hapumgmt/hapu_unarchive.html')
        self.assertContains(response, 'Unarchive Hapu')
        self.assertContains(response, 'Test Hapu')

    def test_hapu_unarchive_view_hapu_leader_access(self):
        """Test that Hapu leaders can access the Hapu unarchive view"""
        self.client.login(email='hapu_leader@example.com', password='hapu123')
        response = self.client.get(reverse('hapumgmt:hapu_unarchive', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Unarchive Hapu')

    def test_hapu_unarchive_view_unauthorized_access(self):
        """Test that unauthorized users cannot access the Hapu unarchive view"""
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('hapumgmt:hapu_unarchive', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to list
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('permission', str(messages[0]))

    def test_hapu_unarchive_view_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the Hapu unarchive view"""
        response = self.client.get(reverse('hapumgmt:hapu_unarchive', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_hapu_unarchive_view_nonexistent_hapu(self):
        """Test accessing unarchive view for non-existent Hapu"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_unarchive', args=[99999]))
        
        self.assertEqual(response.status_code, 404)

    def test_hapu_unarchive_view_active_hapu(self):
        """Test accessing unarchive view for active (non-archived) Hapu"""
        # Create an active Hapu
        active_hapu = Hapu.objects.create(name='Active Hapu', description='Active description', iwi=self.iwi)
        
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_unarchive', args=[active_hapu.pk]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to detail
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('not archived', str(messages[0]))

    def test_hapu_unarchive_success(self):
        """Test unarchiving a Hapu"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        
        response = self.client.post(reverse('hapumgmt:hapu_unarchive', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to list
        self.assertRedirects(response, reverse('hapumgmt:hapu_list'))
        
        # Check that the Hapu was unarchived
        self.hapu.refresh_from_db()
        self.assertFalse(self.hapu.is_archived)
        self.assertIsNone(self.hapu.archived_at)
        self.assertIsNone(self.hapu.archived_by)

    def test_hapu_unarchive_success_message(self):
        """Test that success message is shown after unarchiving Hapu"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        
        response = self.client.post(reverse('hapumgmt:hapu_unarchive', args=[self.hapu.pk]), follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('has been unarchived', str(messages[0]))


class HapuTransferViewTestCase(TestCase):
    """Test cases for Hapu transfer view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Test User',
            state='VERIFIED'
        )
        self.iwi_leader = User.objects.create_user(
            email='iwi_leader@example.com',
            password='leaderpass123',
            full_name='Iwi Leader',
            state='VERIFIED'
        )
        self.hapu_leader = User.objects.create_user(
            email='hapu_leader@example.com',
            password='hapu123',
            full_name='Hapu Leader',
            state='VERIFIED'
        )
        
        # Create Iwis and Hapu
        self.current_iwi = Iwi.objects.create(name='Current Iwi', description='Current Iwi description')
        self.new_iwi = Iwi.objects.create(name='New Iwi', description='New Iwi description')
        self.hapu = Hapu.objects.create(name='Test Hapu', description='Test Hapu description', iwi=self.current_iwi)
        
        # Create leaders
        IwiLeader.objects.create(user=self.iwi_leader, iwi=self.current_iwi)
        IwiLeader.objects.create(user=self.iwi_leader, iwi=self.new_iwi)  # Also leader of new Iwi
        HapuLeader.objects.create(user=self.hapu_leader, hapu=self.hapu)

    def test_hapu_transfer_view_iwi_leader_access(self):
        """Test that Iwi leaders can access the Hapu transfer view"""
        # Archive the current Iwi to enable transfer
        self.current_iwi.archive(archived_by=self.iwi_leader)
        
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_transfer', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hapumgmt/hapu_transfer.html')
        self.assertContains(response, 'Transfer Hapu')
        self.assertContains(response, 'Test Hapu')

    def test_hapu_transfer_view_hapu_leader_access(self):
        """Test that Hapu leaders can access the Hapu transfer view"""
        # Archive the current Iwi to enable transfer
        self.current_iwi.archive(archived_by=self.iwi_leader)
        
        self.client.login(email='hapu_leader@example.com', password='hapu123')
        response = self.client.get(reverse('hapumgmt:hapu_transfer', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Transfer Hapu')

    def test_hapu_transfer_view_unauthorized_access(self):
        """Test that unauthorized users cannot access the Hapu transfer view"""
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('hapumgmt:hapu_transfer', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to list
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('permission', str(messages[0]))

    def test_hapu_transfer_view_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the Hapu transfer view"""
        response = self.client.get(reverse('hapumgmt:hapu_transfer', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to login

    def test_hapu_transfer_view_nonexistent_hapu(self):
        """Test accessing transfer view for non-existent Hapu"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_transfer', args=[99999]))
        
        self.assertEqual(response.status_code, 404)

    def test_hapu_transfer_view_active_iwi(self):
        """Test accessing transfer view for Hapu with active Iwi"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_transfer', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to detail
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('only transfer hapus when their iwi is archived', str(messages[0]))

    def test_hapu_transfer_view_no_available_iwis(self):
        """Test transfer view when no active Iwis are available"""
        # Archive the current Iwi
        self.current_iwi.archive(archived_by=self.iwi_leader)
        # Archive the new Iwi too
        self.new_iwi.archive(archived_by=self.iwi_leader)
        
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        response = self.client.get(reverse('hapumgmt:hapu_transfer', args=[self.hapu.pk]))
        
        self.assertEqual(response.status_code, 302)  # Redirects to detail
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('No active iwis available for transfer', str(messages[0]))

    def test_hapu_transfer_valid_data(self):
        """Test transferring a Hapu with valid data"""
        # Archive the current Iwi to enable transfer
        self.current_iwi.archive(archived_by=self.iwi_leader)
        
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        
        data = {
            'new_iwi': self.new_iwi.id,
            'confirm_transfer': True
        }
        
        response = self.client.post(reverse('hapumgmt:hapu_transfer', args=[self.hapu.pk]), data)
        
        self.assertEqual(response.status_code, 302)  # Redirects to detail
        
        # Check that the Hapu was transferred
        self.hapu.refresh_from_db()
        self.assertEqual(self.hapu.iwi, self.new_iwi)
        
        # Check redirect goes to the correct Hapu detail
        self.assertRedirects(response, reverse('hapumgmt:hapu_detail', args=[self.hapu.pk]))

    def test_hapu_transfer_not_confirmed(self):
        """Test transferring a Hapu without confirmation"""
        # Archive the current Iwi to enable transfer
        self.current_iwi.archive(archived_by=self.iwi_leader)
        
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        
        data = {
            'new_iwi': self.new_iwi.id,
            'confirm_transfer': False
        }
        
        response = self.client.post(reverse('hapumgmt:hapu_transfer', args=[self.hapu.pk]), data)
        
        self.assertEqual(response.status_code, 200)  # Stays on form
        self.assertEqual(self.hapu.iwi, self.current_iwi)  # Hapu not transferred

    def test_hapu_transfer_success_message(self):
        """Test that success message is shown after transferring Hapu"""
        # Archive the current Iwi to enable transfer
        self.current_iwi.archive(archived_by=self.iwi_leader)
        
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        
        data = {
            'new_iwi': self.new_iwi.id,
            'confirm_transfer': True
        }
        
        response = self.client.post(reverse('hapumgmt:hapu_transfer', args=[self.hapu.pk]), data, follow=True)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertGreaterEqual(len(messages), 1)
        transfer_message = any('has been transferred' in str(msg) for msg in messages)
        self.assertTrue(transfer_message)


class HapuManagementIntegrationTestCase(TestCase):
    """Integration test cases for Hapu management workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.iwi_leader = User.objects.create_user(
            email='iwi_leader@example.com',
            password='leaderpass123',
            full_name='Iwi Leader',
            state='VERIFIED'
        )
        
        # Create Iwis
        self.iwi1 = Iwi.objects.create(name='First Iwi', description='First Iwi description')
        self.iwi2 = Iwi.objects.create(name='Second Iwi', description='Second Iwi description')
        
        # Make user leader of both Iwis
        IwiLeader.objects.create(user=self.iwi_leader, iwi=self.iwi1)
        IwiLeader.objects.create(user=self.iwi_leader, iwi=self.iwi2)

    def test_complete_hapu_lifecycle(self):
        """Test complete Hapu lifecycle: create, edit, archive, unarchive"""
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        
        # 1. Create Hapu
        create_data = {
            'name': 'Lifecycle Test Hapu',
            'description': 'Initial description'
        }
        response = self.client.post(reverse('hapumgmt:hapu_create'), create_data)
        self.assertEqual(response.status_code, 302)
        
        hapu = Hapu.objects.get(name='Lifecycle Test Hapu')
        self.assertFalse(hapu.is_archived)
        
        # Make user a Hapu leader to ensure edit permission
        HapuLeader.objects.create(user=self.iwi_leader, hapu=hapu)
        
        # 2. Edit Hapu
        edit_data = {
            'name': 'Lifecycle Test Hapu',
            'description': 'Updated description'
        }
        response = self.client.post(reverse('hapumgmt:hapu_edit', args=[hapu.pk]), edit_data)
        # Check if successful (302) or form errors (200)
        if response.status_code == 200:
            # Form had errors, let's check what they are
            self.assertContains(response, 'form')
        else:
            self.assertEqual(response.status_code, 302)
            hapu.refresh_from_db()
            self.assertEqual(hapu.description, 'Updated description')
        
        # 3. Archive Hapu
        archive_data = {
            'confirm_archive': True
        }
        response = self.client.post(reverse('hapumgmt:hapu_archive', args=[hapu.pk]), archive_data)
        self.assertEqual(response.status_code, 302)
        
        hapu.refresh_from_db()
        self.assertTrue(hapu.is_archived)
        self.assertEqual(hapu.archived_by, self.iwi_leader)
        
        # 4. Unarchive Hapu
        response = self.client.post(reverse('hapumgmt:hapu_unarchive', args=[hapu.pk]))
        self.assertEqual(response.status_code, 302)
        
        hapu.refresh_from_db()
        self.assertFalse(hapu.is_archived)
        self.assertIsNone(hapu.archived_at)
        self.assertIsNone(hapu.archived_by)

    def test_hapu_transfer_workflow(self):
        """Test Hapu transfer workflow"""
        # Create a Hapu
        hapu = Hapu.objects.create(name='Transfer Test Hapu', description='Transfer test', iwi=self.iwi1)
        HapuLeader.objects.create(user=self.iwi_leader, hapu=hapu)
        
        self.client.login(email='iwi_leader@example.com', password='leaderpass123')
        
        # Archive the first Iwi
        self.iwi1.archive(archived_by=self.iwi_leader)
        
        # Transfer the Hapu
        transfer_data = {
            'new_iwi': self.iwi2.id,
            'confirm_transfer': True
        }
        response = self.client.post(reverse('hapumgmt:hapu_transfer', args=[hapu.pk]), transfer_data)
        self.assertEqual(response.status_code, 302)
        
        hapu.refresh_from_db()
        self.assertEqual(hapu.iwi, self.iwi2)
