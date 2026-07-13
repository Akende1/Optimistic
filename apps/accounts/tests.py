from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.sellers.models import Seller
from apps.common.models import LegalAcceptance
from .models import AccountVerificationCode


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
            'accepts_terms': True,
            'accepts_privacy': True,
        }

        response = self.client.post('/api/auth/register/', payload, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], 'BUYER')
        self.assertTrue(User.objects.filter(email='buyer@example.com').exists())
        user = User.objects.get(email='buyer@example.com')
        self.assertEqual(LegalAcceptance.objects.filter(user=user).count(), 2)

    def test_registration_requires_current_legal_acceptance(self):
        response = self.client.post('/api/auth/register/', {
            'full_name':'No Consent','phone_number':'+260971000099','email':'no@example.com',
            'password':'StrongPass123','confirm_password':'StrongPass123','role':'BUYER',
            'accepts_terms':False,'accepts_privacy':False,
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email='no@example.com').exists())

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
            'accepts_terms': True,
            'accepts_privacy': True,
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


class PasswordResetTests(TestCase):
    def test_reset_request_and_confirm_changes_password(self):
        user = User.objects.create_user(username='reset-user', email='reset@example.com', password='old-password')
        client = APIClient()
        request = client.post('/api/v1/auth/password-reset/request/', {'email': user.email}, format='json')
        self.assertEqual(request.status_code, 200)
        challenge = AccountVerificationCode.objects.get(user=user, purpose='PASSWORD_RESET')
        confirm = client.post('/api/v1/auth/password-reset/confirm/', {
            'email': user.email, 'code': challenge.code, 'new_password': 'new-password-123'
        }, format='json')
        self.assertEqual(confirm.status_code, 200, confirm.data)
        user.refresh_from_db()
        self.assertTrue(user.check_password('new-password-123'))

    def test_unknown_email_does_not_disclose_account_existence(self):
        response = APIClient().post('/api/v1/auth/password-reset/request/', {'email': 'missing@example.com'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('debug_code', response.data)
