# pyright: reportAttributeAccessIssue=false
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
from apps.sellers.models import Seller, SellerVerification
from apps.products.models import Product
from apps.notifications.signals import seller_verified
from apps.orders.models import Order
from apps.logistics.models import Delivery, DeliveryPartner
from apps.disputes.models import Dispute
from apps.common.utils import log_audit
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

            try:
                verification = getattr(seller, 'kyc_documents')
            except SellerVerification.DoesNotExist:
                return Response({
                    'error': 'Seller has not submitted KYC documents yet.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            verification.approve(request.user)

            log_audit(
                actor=request.user,
                action='USER_REINSTATE',
                target_type='Seller',
                target_id=seller.id,
                details={'action': 'verify_seller'},
                request=request
            )
            
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

            try:
                verification = getattr(seller, 'kyc_documents')
                verification.reject(request.user, reason or 'Unverified by admin')
            except SellerVerification.DoesNotExist:
                seller.verified = False
                seller.verification_status = 'REJECTED'
                seller.verification_notes = reason
                seller.save(update_fields=['verified', 'verification_status', 'verification_notes'])
            
            # Suspend all active products
            active_products = Product.objects.filter(seller=seller, status='ACTIVE')
            for product in active_products:
                product.suspend(reason=f"Seller unverified: {reason}")
            
            seller.verified = False
            seller.save()

            log_audit(
                actor=request.user, action='USER_SUSPEND', target_type='Seller',
                target_id=seller.id, details={'reason': reason, 'action': 'unverify_seller'},
                request=request,
            )
            
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

    @action(detail=False, methods=['get'], url_path='pending-verifications')
    def pending_verifications(self, request):
        """List sellers with submitted KYC waiting for admin review."""
        verifications = SellerVerification.objects.select_related('seller', 'seller__user', 'reviewed_by').filter(status='PENDING').order_by('-submitted_at')

        data = [{
            'seller_id': item.seller.id,
            'store_name': item.seller.store_name,
            'verification_status': item.seller.verification_status,
            'kyc_status': item.status,
            'submitted_at': item.submitted_at,
            'id_type': item.government_id_type,
            'rejection_reason': item.rejection_reason,
        } for item in verifications]

        return Response({
            'count': len(data),
            'results': data,
        })

    @action(detail=False, methods=['post'], url_path='review-verification/(?P<seller_id>[^/.]+)')
    def review_verification(self, request, seller_id=None):
        """Approve or reject a KYC packet from the moderation endpoint."""
        try:
            seller = Seller.objects.get(id=seller_id)
        except Seller.DoesNotExist:
            return Response({'error': 'Seller not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            verification = getattr(seller, 'kyc_documents')
        except SellerVerification.DoesNotExist:
            return Response({'error': 'Seller has not submitted KYC documents yet.'}, status=status.HTTP_400_BAD_REQUEST)

        action_name = request.data.get('action', '').upper()
        reason = request.data.get('reason', '')

        if action_name == 'APPROVE':
            verification.approve(request.user)
            return Response({'message': 'Seller verification approved.', 'seller_id': seller.id, 'status': seller.verification_status})

        if action_name == 'REJECT':
            if not reason:
                return Response({'error': 'reason is required when rejecting verification.'}, status=status.HTTP_400_BAD_REQUEST)

            verification.reject(request.user, reason)
            Product.objects.filter(seller=seller, status='ACTIVE').update(status='SUSPENDED')
            return Response({'message': 'Seller verification rejected.', 'seller_id': seller.id, 'status': seller.verification_status, 'reason': reason})

        return Response({'error': 'action must be APPROVE or REJECT.'}, status=status.HTTP_400_BAD_REQUEST)
    
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
            'category': p.category.name if p.category else 'Uncategorized',
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

    @action(detail=False, methods=['get'], url_path='audit-logs')
    def audit_logs(self, request):
        """
        List audit logs for admin review.

        GET /api/admin/moderation/audit-logs/?action=USER_SUSPEND&actor=5
        """
        from apps.common.models import AuditLog

        qs = AuditLog.objects.all().order_by('-timestamp')
        action = request.query_params.get('action')
        actor = request.query_params.get('actor')
        target_type = request.query_params.get('target_type')

        if action:
            qs = qs.filter(action=action)
        if actor:
            qs = qs.filter(actor__id=actor)
        if target_type:
            qs = qs.filter(target_type=target_type)

        results = [{
            'id': a.id,
            'actor_id': a.actor.id,
            'actor_username': a.actor.username,
            'action': a.action,
            'target_type': a.target_type,
            'target_id': a.target_id,
            'details': a.details,
            'ip_address': a.ip_address,
            'timestamp': a.timestamp,
        } for a in qs[:200]]

        return Response({'count': qs.count(), 'results': results}, status=status.HTTP_200_OK)


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
        seven_days_ago = timezone.now() - timedelta(days=7)
        
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
        delivered_orders = Order.objects.filter(status='DELIVERED').count()
        total_orders = Order.objects.count()
        average_order_value = float(total_revenue / total_orders) if total_orders else 0.0
        open_disputes = Dispute.objects.filter(status__in=['OPEN', 'EVIDENCE', 'UNDER_REVIEW', 'ESCALATED']).count()
        failed_deliveries = Delivery.objects.filter(status='FAILED').count()
        pending_deliveries = Delivery.objects.filter(status__in=['REQUESTED', 'ASSIGNED', 'PICKED_UP', 'IN_TRANSIT']).count()
        recent_users = [
            {
                'id': user.pk,
                'username': user.username,
                'role': user.role,
                'date_joined': user.date_joined.isoformat(),
                'is_active': user.is_active,
            }
            for user in User.objects.order_by('-date_joined')[:5]
        ]
        recent_orders = [
            {
                'id': order.pk,
                'status': order.status,
                'total_amount': float(order.total_amount),
                'created_at': order.created_at.isoformat(),
            }
            for order in Order.objects.select_related('buyer').order_by('-created_at')[:5]
        ]
        
        metrics = {
            'users': {
                'total': User.objects.count(),
                'buyers': User.objects.filter(role='BUYER').count(),
                'sellers': User.objects.filter(role='SELLER').count(),
                'admins': User.objects.filter(role='ADMIN').count(),
                'new_last_7_days': User.objects.filter(date_joined__gte=seven_days_ago).count(),
            },
            'products': {
                'total': Product.objects.count(),
                'active': Product.objects.filter(status='ACTIVE').count(),
                'pending_approval': Product.objects.filter(status='PENDING_APPROVAL').count(),
                'draft': Product.objects.filter(status='DRAFT').count(),
                'suspended': Product.objects.filter(status='SUSPENDED').count(),
                'archived': Product.objects.filter(status='ARCHIVED').count(),
                'new_last_7_days': Product.objects.filter(created_at__gte=seven_days_ago).count(),
            },
            'orders': {
                'total': total_orders,
                'today': today_orders,
                'pending': Order.objects.filter(status='PENDING').count(),
                'paid': Order.objects.filter(status='PAID').count(),
                'in_transit': Order.objects.filter(status='IN_TRANSIT').count(),
                'delivered': Order.objects.filter(status='DELIVERED').count(),
                'cancelled': Order.objects.filter(status='CANCELLED').count(),
                'completion_rate': round((delivered_orders / total_orders) * 100, 1) if total_orders else 0,
            },
            'revenue': {
                'total': float(total_revenue),
                'month': float(month_revenue),
                'average_order_value': average_order_value,
                'platform_revenue_estimate': float(total_revenue) * 0.05,
            },
            'sellers': {
                'total': Seller.objects.count(),
                'verified': Seller.objects.filter(verified=True).count(),
                'pending_verification': Seller.objects.filter(verified=False).count(),
                'new_last_7_days': Seller.objects.filter(created_at__gte=seven_days_ago).count(),
            },
            'couriers': {
                'total': DeliveryPartner.objects.count(),
                'verified': DeliveryPartner.objects.filter(verified=True, is_active=True).count(),
                'pending_verification': DeliveryPartner.objects.filter(verified=False).count(),
            },
            'disputes': {
                'open': open_disputes,
                'resolved': Dispute.objects.filter(status='RESOLVED').count(),
                'closed': Dispute.objects.filter(status='CLOSED').count(),
            },
            'deliveries': {
                'failed': failed_deliveries,
                'pending': pending_deliveries,
                'delivered': Delivery.objects.filter(status='DELIVERED').count(),
            },
            'recent': {
                'users': recent_users,
                'orders': recent_orders,
            }
        }
        
        return Response(metrics, status=status.HTTP_200_OK)
