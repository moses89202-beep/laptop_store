from django.urls import path
from .views import (
    dashboard_home_view, 
    laptop_manage_view, 
    user_manage_view, 
    order_manage_view
)

urlpatterns = [
    path('', dashboard_home_view, name='dashboard'),
    path('laptops/', laptop_manage_view, name='laptop_manage'),
    path('laptops/<int:pk>/', laptop_manage_view, name='laptop_edit'),
    path('users/', user_manage_view, name='user_manage'),
    path('users/<int:pk>/', user_manage_view, name='user_edit'),
    path('orders/', order_manage_view, name='order_manage'),
    path('orders/<int:pk>/edit/', order_manage_view, name='order_edit'),
]