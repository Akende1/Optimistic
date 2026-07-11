"""Stable metadata endpoints for native mobile clients."""
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .legal import DOCUMENTS, record_acceptance


@api_view(['GET'])
@permission_classes([AllowAny])
def api_meta(request):
    """Return API compatibility and server-time information."""
    return Response({
        'api_version': 'v1',
        'server_time': timezone.now(),
        'currency': 'ZMW',
        'minimum_supported_mobile_version': '1.0.0',
        'features': {
            'inventory_reservations': True,
            'multi_seller_fulfillment': True,
            'buyer_protection': True,
            'mobile_money': True,
        },
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def legal_documents(request):
    return Response({'documents':DOCUMENTS,'counsel_review_required':True})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_legal_document(request):
    document=request.data.get('document')
    if document not in DOCUMENTS: return Response({'error':'Unknown legal document.'},status=400)
    acceptance,created=record_acceptance(user=request.user,document=document,request=request)
    return Response({'accepted':True,'created':created,'document':document,'version':acceptance.version})
