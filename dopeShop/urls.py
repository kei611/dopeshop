
from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),
    path('securelogin/', admin.site.urls),
    # path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
    path('store/', include('store.urls')),
    path('cart/', include('carts.urls')),
    path('terms-and-privacy', views.termsAndPrivacy, name='terms-and-privacy'),

    # ORDERS
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
