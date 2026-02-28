"""
Admin Moderation ViewSet - Platform governance and trust enforcement.

Purpose: Provide admin-only endpoints for moderating marketplace.

Admin Actions:
1. Verify sellers → Enable them to list products
2. Approve products → Make them visible to buyers
3. Suspend products → Hide policy violations
4. Handle reports → Review and take action
5. View system metrics → Monitor platform health

Design Philosophy:
- Admin-only: All endpoints require IsAdminUser permission
- Audit trail: All actions logged (via Django signals)
- Transparent: Clear responses explaining what happened
- Safe: Cannot accidentally break critical data

Usage:
- Called from admin dashboard UI
- RESTful: POST for actions, GET for viewing
- Response includes success message and updated state
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.sellers.models import Seller
from apps.products.models import Product
from apps.notifications.signals import seller_verified
from apps.orders.models import Order
from datetime import datetime, timedelta
from django.db.models import Sum

User = get_user_model()


class AdminModerationViewSet(viewsets.ViewSet):
    """
    Admin moderation endpoints - platform governance.
    
    Base URL: /api/admin/moderation/
    
    All endpoints require admin authentication.
    """
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['post'], url_path='verify-seller/(?P<seller_id>[^/.]+)')
    def verify_seller(self, request, seller_id=None):
        """
        Verify seller account.
        
        POST /api/admin/moderation/verify-seller/{seller_id}/
        
        Business Rules:
        - Only admins can verify sellers
        - Once verified, seller can list products
        - Triggers notification to seller
        - Irreversible (admin must manually unverify if needed)
        
        Response:
            {
                "message": "Seller verified successfully.",
                "seller": {
                    "id": 5,
                    "store_name": "Tech Store Lusaka",
                    "verified": true
                }
            }
        """
        try:
            seller = Seller.objects.get(id=seller_id)
            
            if seller.verified:
                return Response({
                    'error': 'Seller is already verified.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            seller.verified = True
            seller.save()
            
            # Trigger notification signal
            seller_verified.send(sender=self.__class__, seller=seller)
            
            return Response({
                'message': 'Seller verified successfully.',
                'seller': {
                    'id': seller.id,
                    'store_name': seller.store_name,
                    'verified': seller.verified
                }
            }, status=status.HTTP_200_OK)
        
        except Seller.DoesNotExist:
            return Response({
                'error': 'Seller not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='unverify-seller/(?P<seller_id>[^/.]+)')
    def unverify_seller(self, request, seller_id=None):
        """
        Unverify seller account (for policy violations).
        
        POST /api/admin/moderation/unverify-seller/{seller_id}/
        Request body: {"reason": "Repeated policy violations"}
        
        Business Rules:
        - Only admins can unverify
        - All seller's active products automatically suspended
        - Seller cannot create new products until re-verified
        - Triggers notification to seller with reason
        """
        try:
            seller = Seller.objects.get(id=seller_id)
            reason = request.data.get('reason', '')
            
            if not seller.verified:
                return Response({
                    'error': 'Seller is already unverified.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Suspend all active products
            active_products = Product.objects.filter(seller=seller, status='ACTIVE')
            for product in active_products:
                product.suspend(reason=f"Seller unverified: {reason}")
            
            seller.verified = False
            seller.save()
            
            return Response({
                'message': 'Seller unverified and products suspended.',
                'reason': reason,
                'products_suspended': active_products.count(),
                'seller': {
                    'id': seller.id,
                    'store_name': seller.store_name,
                    'verified': seller.verified
                }
            }, status=status.HTTP_200_OK)
        
        except Seller.DoesNotExist:
            return Response({
                'error': 'Seller not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """
        List all products pending approval.
        
        GET /api/admin/moderation/pending-approvals/
        
        Returns: Products with status=PENDING_APPROVAL
        
        Usage: Admin dashboard shows count and list
        """
        products = Product.objects.filter(status='PENDING_APPROVAL').select_related('seller', 'category')
        
        data = [{
            'id': p.id,
            'name': p.name,
            'price': str(p.price),
            'seller': {
                'id': p.seller.id,
                'store_name': p.seller.store_name
            },
            'category': p.category.name,
            'created_at': p.created_at
        } for p in products]
        
        return Response({
            'count': len(data),
            'products': data
        }, status=status.HTTP_200_OK)
    
    # TODO: Implement Report model before enabling this endpoint
    # @action(detail=False, methods=['get'])
    # def pending_reports(self, request):
    #     """
    #     List all open/reviewing reports.
    #     
    #     GET /api/admin/moderation/pending-reports/
    #     
    #     Returns: Reports with status=OPEN or REVIEWING
    #     
    #     Usage: Admin dashboard for report moderation
    #     """
    #     reports = Report.objects.filter(status__in=['OPEN', 'REVIEWING']).select_related('reporter')
    #     
    #     data = [{
    #         'id': r.id,
    #         'target_type': r.target_type,
    #         'target_id': r.target_id,
    #         'reason': r.get_reason_display(),
    #         'description': r.description,
    #         'reporter': r.reporter.username,
    #         'status': r.get_status_display(),
    #         'created_at': r.created_at
    #     } for r in reports]
    #     
    #     return Response({
    #         'count': len(data),
    #         'reports': data
    #     }, status=status.HTTP_200_OK)
    
    # TODO: Implement Report model before enabling this endpoint
    # @action(detail=False, methods=['post'], url_path='handle-report/(?P<report_id>[^/.]+)')
    # def handle_report(self, request, report_id=None):
    #     """
    #     Admin action: Handle a report (action or dismiss).
    #     
    #     POST /api/admin/moderation/handle-report/{report_id}/
    #     Request body: {
    #         "action": "ACTIONED" or "DISMISSED",
    #         "admin_notes": "Explanation of decision",
    #         "suspend_target": true/false
    #     }
    #     
    #     Business Rules:
    #     - Admin reviews report and decides action
    #     - If ACTIONED: Can suspend product/seller
    #     - If DISMISSED: No action taken (false report)
    #     - Admin notes explain decision
    #     - Reporter notified of outcome
    #     """
    #     try:
    #         report = Report.objects.get(id=report_id)
    #         action_taken = request.data.get('action')
    #         admin_notes = request.data.get('admin_notes', '')
    #         suspend_target = request.data.get('suspend_target', False)
    #         
    #         if action_taken not in ['ACTIONED', 'DISMISSED']:
    #             return Response({
    #                 'error': 'Action must be ACTIONED or DISMISSED.'
    #             }, status=status.HTTP_400_BAD_REQUEST)
    #         
    #         # Update report status
    #         report.status = action_taken
    #         report.admin_notes = admin_notes
    #         report.save()
    #         
    #         # Take action on target if requested
    #         if suspend_target and action_taken == 'ACTIONED':
    #             if report.target_type == 'PRODUCT':
    #                 product = Product.objects.get(id=report.target_id)
    #                 product.suspend(reason=f"Report #{report.id}: {report.get_reason_display()}")
    #             elif report.target_type == 'SELLER':
    #                 seller = Seller.objects.get(id=report.target_id)
    #                 seller.verified = False
    #                 seller.save()
    #                 # Suspend all seller's products
    #                 Product.objects.filter(seller=seller, status='ACTIVE').update(status='SUSPENDED')
    #         
    #         return Response({
    #             'message': f'Report {action_taken.lower()}.',
    #             'report': {
    #                 'id': report.id,
    #                 'status': report.get_status_display(),
    #                 'admin_notes': report.admin_notes
    #             },
    #             'target_suspended': suspend_target
    #         }, status=status.HTTP_200_OK)
    #     
    #     except Report.DoesNotExist:
    #         return Response({
    #             'error': 'Report not found.'
    #         }, status=status.HTTP_404_NOT_FOUND)
    #     except Exception as e:
    #         return Response({
    #             'error': str(e)
    #         }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def system_metrics(self, request):
        """
        Get system-wide metrics for admin dashboard.
        
        GET /api/admin/moderation/system-metrics/
        
        Returns:
            {
                "users": {"total": 100, "buyers": 80, "sellers": 20},
                "products": {"total": 500, "active": 450, "pending": 30, "suspended": 20},
                "orders": {"total": 1000, "pending": 10, "in_transit": 5, "delivered": 980},
                "reports": {"open": 5, "reviewing": 3, "actioned": 50, "dismissed": 10}
            }
        """
        from django.contrib.auth import get_user_model
        from apps.orders.models import Order
        
        User = get_user_model()
        
        metrics = {
            'users': {
                'total': User.objects.count(),
                'buyers': User.objects.filter(role='BUYER').count(),
                'sellers': User.objects.filter(role='SELLER').count(),
                'admins': User.objects.filter(role='ADMIN').count()
            },
            'products': {
                'total': Product.objects.count(),
                'active': Product.objects.filter(status='ACTIVE').count(),
                'pending_approval': Product.objects.filter(status='PENDING_APPROVAL').count(),
                'draft': Product.objects.filter(status='DRAFT').count(),
                'suspended': Product.objects.filter(status='SUSPENDED').count(),
                'archived': Product.objects.filter(status='ARCHIVED').count()
            },
            'orders': {
                'total': Order.objects.count(),
                'pending': Order.objects.filter(status='PENDING').count(),
                'paid': Order.objects.filter(status='PAID').count(),
                'in_transit': Order.objects.filter(status='IN_TRANSIT').count(),
                'delivered': Order.objects.filter(status='DELIVERED').count(),
                'cancelled': Order.objects.filter(status='CANCELLED').count()
            },
            # TODO: Add reports metrics when Report model is implemented
            # 'reports': {
            #     'open': Report.objects.filter(status='OPEN').count(),
            #     'reviewing': Report.objects.filter(status='REVIEWING').count(),
            #     'actioned': Report.objects.filter(status='ACTIONED').count(),
            #     'dismissed': Report.objects.filter(status='DISMISSED').count()
            # },
            'sellers': {
                'total': Seller.objects.count(),
                'verified': Seller.objects.filter(verified=True).count(),
                'pending_verification': Seller.objects.filter(verified=False).count()
            }
        }
        
        return Response(metrics, status=status.HTTP_200_OK)


class SystemMetricsView(APIView):
    """
    System metrics API for admin dashboard.
    
    GET /api/admin/metrics/
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Get comprehensive system metrics."""
        today = timezone.now().date()
        this_month_start = timezone.make_aware(datetime(today.year, today.month, 1))
        
        # Calculate total revenue
        total_revenue = Order.objects.filter(
            status__in=['PAID', 'DELIVERED']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Calculate this month's revenue
        month_revenue = Order.objects.filter(
            status__in=['PAID', 'DELIVERED'],
            created_at__gte=this_month_start
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Count today's orders
        today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        today_orders = Order.objects.filter(created_at__gte=today_start).count()
        
        metrics = {
            'users': {
                'total': User.objects.count(),
                'buyers': User.objects.filter(role='BUYER').count(),
                'sellers': User.objects.filter(role='SELLER').count(),
                'admins': User.objects.filter(role='ADMIN').count()
            },
            'products': {
                'total': Product.objects.count(),
                'active': Product.objects.filter(status='ACTIVE').count(),
                'pending_approval': Product.objects.filter(status='PENDING_APPROVAL').count(),
                'draft': Product.objects.filter(status='DRAFT').count(),
                'suspended': Product.objects.filter(status='SUSPENDED').count(),
                'archived': Product.objects.filter(status='ARCHIVED').count()
            },
            'orders': {
                'total': Order.objects.count(),
                'today': today_orders,
                'pending': Order.objects.filter(status='PENDING').count(),
                'paid': Order.objects.filter(status='PAID').count(),
                'in_transit': Order.objects.filter(status='IN_TRANSIT').count(),
                'delivered': Order.objects.filter(status='DELIVERED').count(),
                'cancelled': Order.objects.filter(status='CANCELLED').count()
            },
            'revenue': {
                'total': float(total_revenue),
                'month': float(month_revenue)
            },
            'sellers': {
                'total': Seller.objects.count(),
                'verified': Seller.objects.filter(verified=True).count(),
                'pending_verification': Seller.objects.filter(verified=False).count()
            }
        }
        
        return Response(metrics, status=status.HTTP_200_OK)

