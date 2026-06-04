from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.common.integration_matrix import KNOWN_ALIGNMENT_GAPS, PAGE_ENDPOINT_ALIGNMENT
from apps.sellers.models import Seller


User = get_user_model()
ROOT_DIR = Path(__file__).resolve().parents[3]


class IntegrationAlignmentTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.buyer = User.objects.create_user(
            username='buyer1',
            email='buyer@example.com',
            password='pass1234',
            role='BUYER',
        )
        self.seller_user = User.objects.create_user(
            username='seller1',
            email='seller@example.com',
            password='pass1234',
            role='SELLER',
        )
        self.admin_user = User.objects.create_user(
            username='admin1',
            email='admin@example.com',
            password='pass1234',
            role='ADMIN',
            is_staff=True,
        )
        Seller.objects.create(
            user=self.seller_user,
            store_name='Seller Store',
            phone='0977000000',
            verified=True,
            verification_status='VERIFIED',
        )

    def test_api_v1_and_legacy_paths_are_both_available(self):
        self.assertEqual(self.client.get('/api/categories/').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/categories/').status_code, 200)

    def test_auth_contract_has_standardized_envelope(self):
        response = self.client.post(
            '/api/v1/auth/register/',
            {
                'username': 'newbuyer',
                'email': 'newbuyer@example.com',
                'password': 'pass1234',
                'role': 'BUYER',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])
        self.assertIn('data', response.data)
        self.assertIn('user', response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_role_flow_buyer_seller_admin_access(self):
        self.client.force_authenticate(user=self.buyer)
        self.assertEqual(self.client.get('/api/v1/orders/').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/admin/metrics/').status_code, 403)

        self.client.force_authenticate(user=self.seller_user)
        self.assertEqual(self.client.get('/api/v1/sellers/orders/').status_code, 200)

        self.client.force_authenticate(user=self.admin_user)
        self.assertEqual(self.client.get('/api/v1/admin/metrics/').status_code, 200)

    def test_alignment_matrix_pages_exist(self):
        for section in PAGE_ENDPOINT_ALIGNMENT.values():
            for page in section.keys():
                page_path = ROOT_DIR / 'frontend' / page
                self.assertTrue(page_path.exists(), f'Missing mapped page: {page}')

    def test_known_alignment_gaps_are_explicit_and_unmapped(self):
        mapped_pages = {
            page
            for section in PAGE_ENDPOINT_ALIGNMENT.values()
            for page in section.keys()
        }
        for page in KNOWN_ALIGNMENT_GAPS['missing_pages']:
            self.assertNotIn(page, mapped_pages)
