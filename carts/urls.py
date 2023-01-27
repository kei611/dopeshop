from django.urls import path
from . import views


urlpatterns = [
    path('', views.cart, name='cart'), 
    path('add_cart/<int:product_id>/', views.add_cart, name='add_cart'), 
    path('remove_cart/<int:product_id>/<int:cart_item_id>/', views.remove_cart, name='remove_cart'), 
    path('remove_cart_item/<int:product_id>/<int:cart_item_id>/', views.remove_cart_item, name='remove_cart_item'), 
    path('checkout/', views.checkout, name='checkout'),
    path('webhook/', views.my_webhook_view, name='webhook'),
    # path('order_complete/', views.order_complete, name='order_complete'), 
    path('success/', views.success, name='success'), 
    path('cancel/', views.cancel, name='cancel'), 
]