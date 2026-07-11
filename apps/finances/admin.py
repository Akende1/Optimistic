from django.contrib import admin
from django.http import HttpResponse
import csv
from .models import SellerPayoutRequest, LedgerTransaction, LedgerEntry, EscrowFreeze, OrderFinancialSnapshot, EscrowAccount

class LedgerEntryInline(admin.TabularInline):
    model=LedgerEntry;extra=0;can_delete=False;readonly_fields=('account','side','amount','seller','courier','created_at')

@admin.register(LedgerTransaction)
class LedgerTransactionAdmin(admin.ModelAdmin):
    list_display=('reference','event_type','order','currency','created_at');search_fields=('reference','order__id');readonly_fields=('id','reference','event_type','order','currency','metadata','created_at');inlines=(LedgerEntryInline,)

admin.site.register(EscrowFreeze)
admin.site.register(OrderFinancialSnapshot)
admin.site.register(EscrowAccount)


@admin.register(SellerPayoutRequest)
class SellerPayoutRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller', 'amount', 'provider', 'status', 'requested_at')
    list_filter = ('status', 'provider')
    actions = ('export_selected_csv',)

    @admin.action(description='Export selected payout requests to CSV')
    def export_selected_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="seller-payouts.csv"'
        writer = csv.writer(response)
        writer.writerow(['request_id', 'seller_id', 'store', 'amount', 'provider', 'account_name', 'account_number'])
        for payout in queryset.filter(status__in=['PENDING', 'APPROVED']):
            writer.writerow([payout.id, payout.seller_id, payout.seller.store_name, payout.amount,
                             payout.provider, payout.account_name, payout.account_number])
            payout.status = 'EXPORTED'
            payout.save(update_fields=['status'])
        return response
