from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.sellers.models import Seller


User = get_user_model()


class AuthFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_buyer_returns_tokens_and_profile(self):
        payload = {
            'full_name': 'Test Buyer',
            'phone_number': '+260971000001',
            'email': 'buyer@example.com',
            'password': 'StrongPass123',
            'confirm_password': 'StrongPass123',
            'role': 'BUYER',
        }

        response = self.client.post('/api/auth/register/', payload, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], 'BUYER')
        self.assertTrue(User.objects.filter(email='buyer@example.com').exists())

    def test_register_seller_creates_seller_profile_and_login_redirects(self):
        register_payload = {
            'full_name': 'Test Seller',
            'phone_number': '+260971000002',
            'email': 'seller@example.com',
            'password': 'StrongPass123',
            'confirm_password': 'StrongPass123',
            'role': 'SELLER',
            'seller_type': 'INDIVIDUAL',
            'shop_name': 'Seller Store',
        }

        register_response = self.client.post('/api/auth/register/', register_payload, format='json')
        self.assertEqual(register_response.status_code, 201)
        self.assertTrue(Seller.objects.filter(user__email='seller@example.com').exists())

        login_response = self.client.post(
            '/api/auth/login/',
            {'identifier': 'seller@example.com', 'password': 'StrongPass123'},
            format='json',
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.data['redirect'], '/seller-dashboard-v2.html')
        self.assertEqual(login_response.data['user']['role'], 'SELLER')

    def test_login_buyer_redirects_to_buyer_dashboard(self):
        user = User.objects.create_user(
            username='buyer1',
            email='buyer1@example.com',
            password='StrongPass123',
            role='BUYER',
            phone_number='+260971000003',
        )

        response = self.client.post(
            '/api/auth/login/',
            {'identifier': 'buyer1@example.com', 'password': 'StrongPass123'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['redirect'], '/buyer-dashboard.html')
        self.assertEqual(response.data['user']['id'], user.id)
