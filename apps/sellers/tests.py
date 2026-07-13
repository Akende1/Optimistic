from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient
from apps.logistics.models import ZambianLocation
from .models import Seller, SellerVerification

class SellerKycTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.user=User.objects.create_user(username='kyc-seller',role='SELLER',email='seller@example.com',phone_number='+260970000001',phone_verified=True,email_verified=True)
        self.admin=User.objects.create_superuser(username='kyc-admin',email='admin@example.com',password='pass')
        zone=ZambianLocation.objects.create(name='Kabulonga',location_type='ZONE')
        self.seller=Seller.objects.create(user=self.user,store_name='Trusted Store',phone=self.user.phone_number,business_type='SOLE_TRADER',business_name='Trusted Store',tax_pin='1000000000',physical_address='Plot 1, Kabulonga',primary_location=zone,payout_method='MOBILE_MONEY',payout_provider='MTN_MOMO',payout_account_name='Kyc Seller',payout_account_number=self.user.phone_number)
        image=lambda name:SimpleUploadedFile(name,b'not-a-real-image',content_type='image/jpeg')
        self.verification=SellerVerification.objects.create(seller=self.seller,government_id_type='NRC',government_id_number='123456/78/1',government_id_front=image('front.jpg'),government_id_back=image('back.jpg'),selfie_with_id=image('selfie.jpg'))

    def test_payout_ownership_is_required_before_approval(self):
        self.verification.submit_for_review()
        with self.assertRaises(ValidationError):
            self.verification.approve(self.admin)
        self.seller.payout_account_verified=True
        self.seller.save(update_fields=['payout_account_verified'])
        self.verification.approve(self.admin)
        self.seller.refresh_from_db()
        self.assertTrue(self.seller.can_publish_products())

    def test_sensitive_change_revokes_verified_seller(self):
        self.seller.verified=True;self.seller.verification_status='VERIFIED';self.seller.payout_account_verified=True
        self.seller.save(update_fields=['verified','verification_status','payout_account_verified'])
        from .serializers import SellerUpdateSerializer
        serializer=SellerUpdateSerializer(self.seller,data={'payout_account_number':'+260970000099'},partial=True)
        self.assertTrue(serializer.is_valid(),serializer.errors)
        serializer.save();self.seller.refresh_from_db()
        self.assertFalse(self.seller.verified)
        self.assertFalse(self.seller.payout_account_verified)

    def test_analytics_is_seller_scoped_and_has_mobile_ready_contract(self):
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.get('/api/v1/sellers/analytics/?days=30')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['period']['days'], 30)
        self.assertEqual(response.data['sales']['net'], '0.00')
        self.assertEqual(response.data['products']['total'], 0)
        self.assertIn('balances', response.data)
        self.assertIn('trend', response.data)

    def test_analytics_rejects_invalid_period(self):
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.get('/api/v1/sellers/analytics/?days=month')
        self.assertEqual(response.status_code, 400)
