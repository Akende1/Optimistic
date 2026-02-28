"""
System Reports API - Data exports and analytics
"""
import csv
import json
from io import StringIO
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, F
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import get_user_model
from apps.products.models import Product
from apps.orders.models import Order
from apps.sellers.models import Seller
from apps.disputes.models import Dispute

User = get_user_model()


def parse_date_range(request):
    """Parse date range from request parameters"""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if start_date:
        start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
    else:
        start_date = timezone.now() - timedelta(days=30)
    
    if end_date:
        end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
    else:
        end_date = timezone.now()
    
    return start_date, end_date


@api_view(['GET'])
@permission_classes([IsAdminUser])
def gmv_report(request):
    """
    GMV Report - Total gross merchandise value
    GET /api/admin/reports/gmv/
    
    Query params:
    - start_date: YYYY-MM-DD
    - end_date: YYYY-MM-DD
    - format: json (default) or csv
    - seller_id: Filter by seller
    - category_id: Filter by category
    """
    start_date, end_date = parse_date_range(request)
    format_type = request.query_params.get('format', 'json')
    
    # Base query
    orders = Order.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date,
        status__in=['PAID', 'DELIVERED']
    )
    
    # Apply filters
    seller_id = request.query_params.get('seller_id')
    if seller_id:
        orders = orders.filter(seller_id=seller_id)
    
    # Aggregate by date
    daily_gmv = orders.extra(
        select={'date': 'DATE(created_at)'}
    ).values('date').annotate(
        total_gmv=Sum('total_amount'),
        order_count=Count('id')
    ).order_by('date')
    
    # Calculate totals
    total_gmv = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    total_orders = orders.count()
    
    data = {
        'period': {
            'start': start_date.date().isoformat(),
            'end': end_date.date().isoformat()
        },
        'summary': {
            'total_gmv': float(total_gmv),
            'total_orders': total_orders,
            'average_order_value': float(total_gmv / total_orders) if total_orders > 0 else 0
        },
        'daily_breakdown': list(daily_gmv)
    }
    
    if format_type == 'csv':
        return export_csv(daily_gmv, 'gmv_report', ['date', 'total_gmv', 'order_count'])
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def revenue_report(request):
    """
    Platform Revenue Report - Commission breakdown
    GET /api/admin/reports/revenue/
    """
    start_date, end_date = parse_date_range(request)
    format_type = request.query_params.get('format', 'json')
    
    orders = Order.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date,
        status__in=['PAID', 'DELIVERED']
    )
    
    total_gmv = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    platform_fee_rate = 0.05  # 5% commission
    platform_revenue = float(total_gmv) * platform_fee_rate
    
    data = {
        'period': {
            'start': start_date.date().isoformat(),
            'end': end_date.date().isoformat()
        },
        'revenue': {
            'total_gmv': float(total_gmv),
            'platform_commission': platform_revenue,
            'commission_rate': platform_fee_rate,
            'seller_earnings': float(total_gmv) - platform_revenue
        },
        'breakdown': {
            'orders_count': orders.count(),
            'average_commission_per_order': platform_revenue / orders.count() if orders.count() > 0 else 0
        }
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_growth_report(request):
    """
    User Growth Report - Registration trends
    GET /api/admin/reports/user-growth/
    """
    start_date, end_date = parse_date_range(request)
    
    # Daily registrations
    daily_users = User.objects.filter(
        date_joined__gte=start_date,
        date_joined__lte=end_date
    ).extra(
        select={'date': 'DATE(date_joined)'}
    ).values('date', 'role').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Role distribution
    role_distribution = User.objects.values('role').annotate(
        count=Count('id')
    )
    
    # Total users
    total_users = User.objects.count()
    period_users = User.objects.filter(
        date_joined__gte=start_date,
        date_joined__lte=end_date
    ).count()
    
    data = {
        'period': {
            'start': start_date.date().isoformat(),
            'end': end_date.date().isoformat()
        },
        'summary': {
            'total_users': total_users,
            'new_users_in_period': period_users
        },
        'role_distribution': list(role_distribution),
        'daily_registrations': list(daily_users)
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def seller_performance_report(request):
    """
    Seller Performance Report - Sales rankings
    GET /api/admin/reports/seller-performance/
    """
    from apps.orders.models import OrderItem
    
    start_date, end_date = parse_date_range(request)
    
    # Top sellers by GMV (through OrderItem)
    top_sellers = OrderItem.objects.filter(
        order__created_at__gte=start_date,
        order__created_at__lte=end_date,
        order__status__in=['PAID', 'DELIVERED']
    ).values(
        'seller__store_name',
        'seller__id',
        'seller__user__email'
    ).annotate(
        total_sales=Sum(F('quantity') * F('price_snapshot')),
        order_count=Count('order__id', distinct=True),
        items_sold=Sum('quantity')
    ).order_by('-total_sales')[:20]
    
    data = {
        'period': {
            'start': start_date.date().isoformat(),
            'end': end_date.date().isoformat()
        },
        'top_sellers': [
            {
                'store_name': seller['seller__store_name'],
                'seller_id': seller['seller__id'],
                'email': seller['seller__user__email'],
                'total_sales': float(seller['total_sales'] or 0),
                'order_count': seller['order_count'],
                'items_sold': seller['items_sold']
            }
            for seller in top_sellers
        ]
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def product_metrics_report(request):
    """
    Product Metrics Report - Listing volumes
    GET /api/admin/reports/product-metrics/
    """
    start_date, end_date = parse_date_range(request)
    
    # Products by status
    status_distribution = Product.objects.values('status').annotate(
        count=Count('id')
    )
    
    # Products by category
    category_distribution = Product.objects.values('category__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # New products in period
    new_products = Product.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    ).count()
    
    data = {
        'period': {
            'start': start_date.date().isoformat(),
            'end': end_date.date().isoformat()
        },
        'summary': {
            'total_products': Product.objects.count(),
            'new_products_in_period': new_products
        },
        'status_distribution': list(status_distribution),
        'top_categories': list(category_distribution)
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def financial_audit_report(request):
    """
    Financial Audit Report - Escrow and commission tracking
    GET /api/admin/reports/financial-audit/
    """
    from apps.finances.models import EscrowAccount
    
    start_date, end_date = parse_date_range(request)
    
    # Aggregate escrow balances
    escrow_summary = EscrowAccount.objects.aggregate(
        total_available=Sum('available_balance'),
        total_pending=Sum('pending_balance'),
        total_lifetime=Sum('lifetime_earnings')
    )
    
    # Top earning sellers
    top_earners = EscrowAccount.objects.select_related('seller').order_by(
        '-lifetime_earnings'
    )[:10].values(
        'seller__store_name',
        'seller__id',
        'available_balance',
        'pending_balance',
        'lifetime_earnings',
        'last_payout_at'
    )
    
    data = {
        'period': {
            'start': start_date.date().isoformat(),
            'end': end_date.date().isoformat()
        },
        'escrow_summary': {
            'total_available': float(escrow_summary['total_available'] or 0),
            'total_pending': float(escrow_summary['total_pending'] or 0),
            'total_lifetime_earnings': float(escrow_summary['total_lifetime'] or 0)
        },
        'top_earners': [
            {
                'store_name': e['seller__store_name'],
                'seller_id': e['seller__id'],
                'available_balance': float(e['available_balance']),
                'pending_balance': float(e['pending_balance']),
                'lifetime_earnings': float(e['lifetime_earnings']),
                'last_payout': e['last_payout_at'].isoformat() if e['last_payout_at'] else None
            }
            for e in top_earners
        ]
    }
    
    return Response(data)


def export_csv(data, filename, fieldnames):
    """Export data as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}_{timezone.now().date()}.csv"'
    
    writer = csv.DictWriter(response, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)
    
    return response


@api_view(['GET'])
@permission_classes([IsAdminUser])
def export_audit_logs(request):
    """
    Export audit logs
    GET /api/admin/reports/audit-logs/
    """
    from apps.common.models import AuditLog
    
    start_date, end_date = parse_date_range(request)
    format_type = request.query_params.get('format', 'json')
    
    logs = AuditLog.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    ).select_related('actor').values(
        'id', 'actor__username', 'action', 'target_type', 
        'target_id', 'timestamp', 'ip_address'
    )
    
    if format_type == 'csv':
        return export_csv(
            logs, 
            'audit_logs', 
            ['id', 'actor__username', 'action', 'target_type', 'target_id', 'timestamp', 'ip_address']
        )
    
    return Response({
        'period': {
            'start': start_date.date().isoformat(),
            'end': end_date.date().isoformat()
        },
        'logs': list(logs)
    })
