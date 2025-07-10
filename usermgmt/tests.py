from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Iwi, Hapu
from core.models import CustomUser

User = get_user_model()

class UserListViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('usermgmt:user_list')
        self.iwi = Iwi.objects.create(name='Test Iwi', description='Test Iwi')
        self.hapu = Hapu.objects.create(name='Test Hapu', iwi=self.iwi, description='Test Hapu')
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='adminpass',
            full_name='Admin User',
            is_staff=True,
            state='VERIFIED'
        )
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='userpass1',
            full_name='User One',
            iwi=self.iwi,
            hapu=self.hapu,
            state='PENDING_VERIFICATION'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='userpass2',
            full_name='User Two',
            iwi=self.iwi,
            hapu=self.hapu,
            state='VERIFIED'
        )

    def test_user_list_requires_admin(self):
        # Not logged in
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        # Not admin
        self.client.login(email='user1@example.com', password='userpass1')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_user_list_get(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User Management')
        self.assertContains(response, 'User One')
        self.assertContains(response, 'User Two')

    def test_user_list_filter_by_state(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url + '?state=VERIFIED')
        self.assertContains(response, 'User Two')
        self.assertNotContains(response, 'User One')

    def test_user_list_verify_user(self):
        self.client.force_login(self.admin)
        data = {'verify_user_id': str(self.user1.id)}
        response = self.client.post(self.url, data, follow=True)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.state, 'VERIFIED')
        self.assertContains(response, 'has been verified successfully')

    def test_user_list_reject_user(self):
        self.client.force_login(self.admin)
        data = {'reject_user_id': str(self.user1.id)}
        response = self.client.post(self.url, data, follow=True)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.state, 'REJECTED')
        self.assertContains(response, 'has been rejected successfully')
