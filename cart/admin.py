from django.contrib import admin
from django.utils.html import format_html
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['added_at', 'get_total_price']
    fields = ['product', 'quantity', 'added_at', 'get_total_price']

    def get_total_price(self, obj):
        if obj.pk:
            return format_html('<strong>{:,} ₽</strong>', int(obj.get_total_price()))
        return '-'
    get_total_price.short_description = "Сумма"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_total_items_display', 'get_total_price_display', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    inlines = [CartItemInline]
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'updated_at'

    def get_total_items_display(self, obj):
        count = obj.get_total_items()
        return format_html(
            '<span style="background: #20B2AA; color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 500;">{} шт</span>',
            count
        )
    get_total_items_display.short_description = "Товаров"

    def get_total_price_display(self, obj):
        price = obj.get_total_price()
        return format_html('<strong style="color: #20B2AA; font-size: 14px;">{:,} ₽</strong>', int(price))
    get_total_price_display.short_description = "Итого"
    get_total_price_display.admin_order_field = 'updated_at'
