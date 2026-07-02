from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from myapp import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('catalog/', views.laptop_catalog, name='laptop_catalog'),
    path('cart/', views.cart_page, name='cart_page'),
    path('api/cart-items/', views.cart_items_api, name='cart_items_api'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
