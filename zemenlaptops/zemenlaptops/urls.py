from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from myapp import views
from dashboard.views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('catalog/', views.laptop_catalog, name='laptop_catalog'),
    path('cart/', views.cart_page, name='cart_page'),
    path('dashboard/', dashboard_home_view, name='dashboard'),
    path('api/cart-items/', views.cart_items_api, name='cart_items_api'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/', views.profile_view, name='profile'),
    # Laptop URLs (Handles CRUD + Review Read/Delete seamlessly via unique template actions)
    path('laptops/', laptop_manage_view, name='laptop_manage'),
    path('laptops/<int:pk>/', laptop_manage_view, name='laptop_edit'),

    # User URLs
    path('users/', user_manage_view, name='user_manage'),
    path('users/<int:pk>/', user_manage_view, name='user_edit'),

    # Order URLs
    path('orders/', order_manage_view, name='order_manage'),
    path('orders/<int:pk>/', order_manage_view, name='order_edit'),
    path('review/update/<int:review_id>/', views.update_review, name='update_review'),
    path('review/delete/<int:review_id>/', views.delete_review, name='delete_review'),
    path('profile/delete/', views.delete_account_view, name='delete_account'),
        path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
            success_url="/password-reset/done/",
        ),
        name="password_reset",
    ),

    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),

    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url="/reset/done/",
        ),
        name="password_reset_confirm",
    ),

    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("payment/", include("app2.urls")),

    # urls.py
path('laptop/<int:pk>/', views.laptop_detail, name='laptop_detail'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
