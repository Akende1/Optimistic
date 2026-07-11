from django.contrib import admin
from .models import AuditLog, OutboxEvent, ProcessedEvent, LegalAcceptance

@admin.register(LegalAcceptance)
class LegalAcceptanceAdmin(admin.ModelAdmin):
    list_display=('user','document','version','accepted_at','ip_address');list_filter=('document','version');search_fields=('user__username','user__email','content_hash');readonly_fields=('user','document','version','content_hash','ip_address','user_agent','accepted_at')

@admin.register(OutboxEvent)
class OutboxEventAdmin(admin.ModelAdmin):
    list_display=('topic','aggregate_type','aggregate_id','status','attempts','available_at','created_at')
    list_filter=('status','topic');search_fields=('idempotency_key','aggregate_id','last_error');readonly_fields=('id','topic','aggregate_type','aggregate_id','idempotency_key','payload','attempts','locked_at','published_at','last_error','created_at')

@admin.register(ProcessedEvent)
class ProcessedEventAdmin(admin.ModelAdmin):
    list_display=('consumer','event','processed_at');readonly_fields=('consumer','event','processed_at')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display=('actor','action','target_type','target_id','timestamp');list_filter=('action','target_type');readonly_fields=('actor','action','target_type','target_id','details','ip_address','timestamp')
