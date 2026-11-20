from . import views
from django.urls import path, include

urlpatterns = [
    path('initialize/', views.initialize_payment, name='initialize_payment'),
    path('success/<str:tx_ref>/', views.verify_payment, name='verify_payment'),
]