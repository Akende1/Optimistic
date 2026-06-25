from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.api import get_user_seller
from apps.common.permissions import IsVerifiedSeller
from .models import RfqRequest, SupplierQuote
from .serializers import RfqRequestSerializer, SupplierQuoteSerializer, RfqAwardSerializer


class RfqRequestViewSet(viewsets.ModelViewSet):
    serializer_class = RfqRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = RfqRequest.objects.prefetch_related('items', 'quotes__seller').select_related('buyer', 'awarded_quote')

        if user.is_staff:
            return qs

        if user.role == 'SELLER':
            return qs.filter(status='OPEN', response_deadline__gte=timezone.now())

        return qs.filter(buyer=user)

    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsVerifiedSeller])
    @transaction.atomic
    def submit_quote(self, request, pk=None):
        rfq = self.get_object()
        seller = get_user_seller(request.user)
        if seller is None:
            return Response({'error': 'Seller profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not rfq.is_open_for_quotes:
            return Response({'error': 'RFQ is not open for quoting.'}, status=status.HTTP_400_BAD_REQUEST)

        if rfq.quotes.filter(seller=seller).exists():
            return Response({'error': 'You already submitted a quote for this RFQ.'}, status=status.HTTP_400_BAD_REQUEST)

        payload = dict(request.data)
        payload['rfq'] = rfq.id
        serializer = SupplierQuoteSerializer(data=payload, context={'request': request, 'seller': seller})
        serializer.is_valid(raise_exception=True)
        quote = serializer.save(rfq=rfq)

        return Response(SupplierQuoteSerializer(quote, context={'request': request}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def quotes(self, request, pk=None):
        rfq = self.get_object()
        if request.user != rfq.buyer and not request.user.is_staff:
            return Response({'error': 'Only the RFQ owner can view all quotes.'}, status=status.HTTP_403_FORBIDDEN)

        quotes = rfq.quotes.prefetch_related('items', 'seller').all()
        data = SupplierQuoteSerializer(quotes, many=True, context={'request': request}).data
        return Response({'count': len(data), 'results': data})

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def award(self, request, pk=None):
        rfq = self.get_object()
        if request.user != rfq.buyer and not request.user.is_staff:
            return Response({'error': 'Only the RFQ owner can award quotes.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = RfqAwardSerializer(data=request.data, context={'rfq': rfq})
        serializer.is_valid(raise_exception=True)
        quote = rfq.quotes.get(id=serializer.validated_data['quote_id'])

        rfq.awarded_quote = quote
        rfq.status = 'AWARDED'
        rfq.save(update_fields=['awarded_quote', 'status', 'updated_at'])

        rfq.quotes.exclude(id=quote.id).update(status='LOST')
        quote.status = 'WON'
        quote.save(update_fields=['status', 'updated_at'])

        return Response({'message': 'Quote awarded successfully.', 'awarded_quote_id': quote.id})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsVerifiedSeller])
    def my_quotes(self, request):
        seller = get_user_seller(request.user)
        if seller is None:
            return Response({'error': 'Seller profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        quotes = SupplierQuote.objects.filter(seller=seller).select_related('rfq')
        data = SupplierQuoteSerializer(quotes, many=True, context={'request': request}).data
        return Response({'count': len(data), 'results': data})
