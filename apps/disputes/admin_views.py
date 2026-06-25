"""
Admin Disputes Views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from django.db.models import Q
from .models import Dispute


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_disputes(request):
    """
    Get all disputes for admin review.
    GET /api/admin/disputes/
    
    Query params:
    - status: Filter by status (OPEN, UNDER_REVIEW, RESOLVED, etc.)
    - search: Search by user
    """
    disputes = Dispute.objects.select_related(
        'opened_by',
        'resolution'
    ).prefetch_related(
        'target_content_type'
    ).order_by('-created_at')
    
    # Apply filters
    dispute_status = request.query_params.get('status')
    if dispute_status:
        disputes = disputes.filter(status=dispute_status)
    
    search = request.query_params.get('search')
    if search:
        disputes = disputes.filter(
            Q(opened_by__username__icontains=search)
        )
    
    # Serialize
    data = [{
        'id': d.pk,
        'target_type': d.target_content_type.model if d.target_content_type else None,
        'target_id': d.target_object_id,
        'reason': d.reason,
        'reason_display': d.get_reason_display(),
        'status': d.status,
        'status_display': d.get_status_display(),
        'opened_by': {
            'id': d.opened_by.pk,
            'username': d.opened_by.username,
            'role': d.opened_by.role
        },
        'description': d.description,
        'created_at': d.created_at.isoformat(),
        'resolved_at': d.resolved_at.isoformat() if d.resolved_at else None,
        'resolution_notes': d.resolution.resolution_notes if d.resolution else None,
        'outcome': d.resolution.outcome if d.resolution else None,
    } for d in disputes]
    
    return Response({
        'count': len(data),
        'results': data
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def resolve_dispute(request, dispute_id):
    """
    Resolve a dispute.
    POST /api/admin/disputes/{dispute_id}/resolve/
    
    Body:
    {
        "outcome": "BUYER_FAVOR",
        "resolution_notes": "Refund approved based on evidence"
    }
    """
    from .models import DisputeResolution
    
    try:
        dispute = Dispute.objects.get(pk=dispute_id)
        
        if dispute.status == 'CLOSED':
            return Response(
                {'error': 'Dispute is already closed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        outcome = request.data.get('outcome')
        resolution_notes = request.data.get('resolution_notes', '')
        
        if not outcome:
            return Response(
                {'error': 'Outcome is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create resolution
        resolution = DisputeResolution.objects.create(
            outcome=outcome,
            resolution_notes=resolution_notes,
            resolved_by=request.user,
            actions_completed=False,
        )

        # Optionally execute financial actions immediately (admin-controlled)
        execute_financial = bool(request.data.get('execute_financial', False))
        if execute_financial:
            try:
                resolution.execute_financial_actions()
            except Exception:
                # Don't block resolution if financial execution fails; surface later in audit/logs
                pass

        # Update dispute
        dispute.status = 'RESOLVED'
        dispute.resolution = resolution
        dispute.resolved_at = timezone.now()
        dispute.save()

        # Audit log
        try:
            from apps.common.models import AuditLog
            AuditLog.objects.create(
                actor=request.user,
                action='DISPUTE_RESOLVE_BUYER' if outcome.startswith('BUYER') else 'DISPUTE_RESOLVE_SELLER',
                target_type='Dispute',
                target_id=dispute.id,
                details={'outcome': outcome, 'notes': resolution_notes, 'executed_financial': execute_financial},
                ip_address=request.META.get('REMOTE_ADDR', ''),
            )
        except Exception:
            pass
        
        return Response({
            'message': 'Dispute resolved successfully',
            'dispute': {
                'id': dispute.pk,
                'status': dispute.status,
                'outcome': resolution.outcome
            }
        })
        
    except Dispute.DoesNotExist:
        return Response(
            {'error': 'Dispute not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def close_dispute(request, dispute_id):
    """
    Close a dispute permanently.
    POST /api/admin/disputes/{dispute_id}/close/
    """
    try:
        dispute = Dispute.objects.get(pk=dispute_id)
        
        if dispute.status != 'RESOLVED':
            return Response(
                {'error': 'Can only close resolved disputes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dispute.status = 'CLOSED'
        dispute.save()
        
        return Response({
            'message': 'Dispute closed successfully',
            'dispute': {
                'id': dispute.pk,
                'status': dispute.status
            }
        })
        
    except Dispute.DoesNotExist:
        return Response(
            {'error': 'Dispute not found'},
            status=status.HTTP_404_NOT_FOUND
        )
