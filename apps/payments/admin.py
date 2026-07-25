from django.contrib import admin
from .models import Transaction, PaymentMethod


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('user__username', 'transaction_id')
    ordering = ('-created_at',)
    readonly_fields = ('transaction_id', 'created_at', 'completed_at')


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'last_four', 'is_default', 'active', 'created_at')
    list_filter = ('type', 'active', 'is_default', 'created_at')
    search_fields = ('user__username', 'nickname')
    readonly_fields = ('stripe_payment_method_id', 'created_at')
