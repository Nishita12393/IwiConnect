from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages
from unittest.mock import patch
from .models import Iwi, Hapu, PasswordResetToken

User = get_user_model()


class UserRegistrationTestCase(TestCase):
    """Test cases for user registration functionality"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        
        # Create test Iwi and Hapu
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi Description')
        self.hapu = Hapu.objects.create(name='Test Hapu', iwi=self.iwi, description='Test Hapu Description')
        
        # Create test file
        self.test_file = SimpleUploadedFile(
            "test_document.pdf",
            b'Test file content',
            content_type="application/pdf"
        )
        
        # Valid registration data
        self.valid_data = {
            'full_name': 'John Doe',
            'email': 'john.doe@example.com',
            'password': 'testpassword123',
            'iwi': self.iwi.id,
            'hapu': self.hapu.id,
        }

    def test_register_page_loads(self):
        """Test that registration page loads correctly"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        self.assertContains(response, 'Register')

    def test_successful_registration(self):
        """Test successful user registration"""
        data = self.valid_data.copy()
        data['citizenship_document'] = self.test_file
        
        response = self.client.post(self.register_url, data)
        
        self.assertRedirects(response, self.register_url)
        
        # Check that user was created
        user = User.objects.get(email='john.doe@example.com')
        self.assertEqual(user.full_name, 'John Doe')
        self.assertEqual(user.state, 'PENDING_VERIFICATION')
        self.assertEqual(user.iwi, self.iwi)
        self.assertEqual(user.hapu, self.hapu)
        self.assertTrue(user.check_password('testpassword123'))
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Thank you for registering', str(messages[0]))

    def test_registration_duplicate_email(self):
        """Test registration with existing email"""
        User.objects.create_user(
            email='john.doe@example.com',
            password='testpass123',
            full_name='Existing User',
            state='VERIFIED'
        )
        
        data = self.valid_data.copy()
        data['citizenship_document'] = self.test_file
        
        response = self.client.post(self.register_url, data)
        
        self.assertRedirects(response, self.register_url)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Please correct the errors', str(messages[0]))

    def test_registration_invalid_email(self):
        """Test registration with invalid email format"""
        data = self.valid_data.copy()
        data['email'] = 'invalid-email'
        data['citizenship_document'] = self.test_file
        
        response = self.client.post(self.register_url, data)
        
        self.assertRedirects(response, self.register_url)
        self.assertFalse(User.objects.filter(email='invalid-email').exists())

    def test_registration_short_password(self):
        """Test registration with password less than 8 characters"""
        data = self.valid_data.copy()
        data['password'] = 'short'
        data['citizenship_document'] = self.test_file
        
        response = self.client.post(self.register_url, data)
        
        self.assertRedirects(response, self.register_url)
        self.assertFalse(User.objects.filter(email='john.doe@example.com').exists())

    def test_registration_without_citizenship_document(self):
        """Test registration without citizenship document"""
        data = self.valid_data.copy()
        
        response = self.client.post(self.register_url, data)
        
        self.assertRedirects(response, self.register_url)
        self.assertFalse(User.objects.filter(email='john.doe@example.com').exists())

    def test_registration_authenticated_user_redirect(self):
        """Test that authenticated users are redirected from registration page"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User',
            state='VERIFIED'
        )
        self.client.force_login(user)
        
        response = self.client.get(self.register_url)
        self.assertRedirects(response, reverse('dashboard'))

    @patch('core.views.send_welcome_email')
    def test_welcome_email_sent_on_registration(self, mock_send_email):
        """Test that welcome email is sent on successful registration"""
        data = self.valid_data.copy()
        data['citizenship_document'] = self.test_file
        
        response = self.client.post(self.register_url, data)
        
        mock_send_email.assert_called_once()
        user = User.objects.get(email='john.doe@example.com')
        mock_send_email.assert_called_with(user)


class UserLoginTestCase(TestCase):
    """Test cases for user login functionality"""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.dashboard_url = reverse('dashboard')
        
        # Create test Iwi
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi Description')
        
        # Create test users
        self.verified_user = User.objects.create_user(
            email='verified@example.com',
            password='testpass123',
            full_name='Verified User',
            state='VERIFIED'
        )
        
        self.pending_user = User.objects.create_user(
            email='pending@example.com',
            password='testpass123',
            full_name='Pending User',
            state='PENDING_VERIFICATION'
        )
        
        self.rejected_user = User.objects.create_user(
            email='rejected@example.com',
            password='testpass123',
            full_name='Rejected User',
            state='REJECTED'
        )

    def test_login_page_loads(self):
        """Test that login page loads correctly"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertContains(response, 'Login')

    def test_successful_login_verified_user(self):
        """Test successful login for verified user"""
        data = {
            'email': 'verified@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertRedirects(response, self.dashboard_url)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user, self.verified_user)

    def test_login_pending_user(self):
        """Test login attempt for pending verification user"""
        data = {
            'email': 'pending@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertRedirects(response, self.login_url)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('not verified yet', str(messages[0]))

    def test_login_rejected_user(self):
        """Test login attempt for rejected user"""
        data = {
            'email': 'rejected@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertRedirects(response, self.login_url)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('not verified yet', str(messages[0]))

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            'email': 'verified@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertRedirects(response, self.login_url)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Invalid email or password', str(messages[0]))

    def test_login_nonexistent_user(self):
        """Test login with non-existent user"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertRedirects(response, self.login_url)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Invalid email or password', str(messages[0]))

    def test_login_empty_fields(self):
        """Test login with empty fields"""
        data = {
            'email': '',
            'password': ''
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_invalid_email_format(self):
        """Test login with invalid email format"""
        data = {
            'email': 'invalid-email',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_authenticated_user_redirect(self):
        """Test that authenticated users are redirected from login page"""
        self.client.force_login(self.verified_user)
        
        response = self.client.get(self.login_url)
        self.assertRedirects(response, self.dashboard_url)

    def test_login_case_insensitive_email(self):
        """Test that email login is case insensitive"""
        data = {
            'email': 'VERIFIED@EXAMPLE.COM',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertRedirects(response, self.dashboard_url)
        self.assertTrue(response.wsgi_request.user.is_authenticated) 