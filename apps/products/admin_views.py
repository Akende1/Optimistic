"""
Admin Product Moderation Views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from .models import Product


@api_view(['POST'])
@permission_classes([IsAdminUser])
def approve_product(request, product_id):
    """
    Approve a product for public listing.
    POST /api/admin/products/{product_id}/approve/
    """
    try:
        product = Product.objects.get(pk=product_id)
        
        if product.status == 'ACTIVE':
            return Response(
                {'error': 'Product is already active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product.status = 'ACTIVE'
        product.save()
        
        return Response({
            'message': 'Product approved successfully',
            'product': {
                'id': product.pk,
                'name': product.name,
                'status': product.status
            }
        })
        
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def suspend_product(request, product_id):
    """
    Suspend a product (remove from public view).
    POST /api/admin/products/{product_id}/suspend/
    
    Body:
    {
        "reason": "Violates policy: prohibited items"
    }
    """
    try:
        product = Product.objects.get(pk=product_id)
        
        if product.status == 'SUSPENDED':
            return Response(
                {'error': 'Product is already suspended'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', 'Policy violation')
        
        product.status = 'SUSPENDED'
        product.save()
        
        # TODO: Store suspension reason in a ProductModerationLog model
        
        return Response({
            'message': 'Product suspended successfully',
            'product': {
                'id': product.pk,
                'name': product.name,
                'status': product.status
            }
        })
        
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def flag_product(request, product_id):
    """
    Flag a product for review (mark as problematic but keep active).
    POST /api/admin/products/{product_id}/flag/
    
    Body:
    {
        "reason": "Suspected counterfeit",
        "severity": "HIGH"
    }
    """
    try:
        product = Product.objects.get(pk=product_id)
        
        reason = request.data.get('reason', 'Flagged for review')
        severity = request.data.get('severity', 'MEDIUM')
        
        # TODO: Create ProductFlag model to track flagged products
        # For now, we'll just return success
        
        return Response({
            'message': 'Product flagged successfully',
            'product': {
                'id': product.pk,
                'name': product.name,
                'status': product.status
            },
            'flag': {
                'reason': reason,
                'severity': severity,
                'flagged_by': request.user.username
            }
        })
        
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def archive_product(request, product_id):
    """
    Archive a product (keep in database but hide from all views).
    POST /api/admin/products/{product_id}/archive/
    """
    try:
        product = Product.objects.get(pk=product_id)
        
        product.status = 'ARCHIVED'
        product.save()
        
        return Response({
            'message': 'Product archived successfully',
            'product': {
                'id': product.pk,
                'name': product.name,
                'status': product.status
            }
        })
        
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )
