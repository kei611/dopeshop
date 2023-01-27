from django.contrib import admin
from .models import Cart, CartItem, Order, Payment

# Register your models here.
class CartAdmin(admin.ModelAdmin):
    list_display = ('cart_id', 'date_added')
    
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'cart', 'quantity', 'is_active')
    
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'phone', 'email', 'city', 'order_total', 'status', 'is_ordered', 'created_at']
    list_filter = ['status', 'is_ordered']
    search_fields = ['order_number', 'full_name', 'phone', 'email']
    list_per_page = 20


admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)

admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)