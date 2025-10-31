"""
URL configuration for roadmate1 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from app1.views import (home, custom_login, signup, custom_logout, 
                      fuel_service_providers, towing_service, mechanic_service, 
                      battery_service, tire_service, lockout_service, provider_register,
                      admin_dashboard, provider_dashboard, create_service_request, update_service_request,
                      user_profile, my_bookings)
from app1.admin_site import custom_admin_site

urlpatterns = [
    path('', home, name='home'),
    path('admin/', custom_admin_site.urls),  # Use our custom admin site
    
    # Authentication URLs
    path('login/', custom_login, name='login'),
    path('logout/', custom_logout, name='logout'),
    path('signup/', signup, name='signup'),
    
    # User URLs
    path('profile/', user_profile, name='user_profile'),
    path('my-bookings/', my_bookings, name='my_bookings'),
    
    # Service URLs
    path('services/fuel/', fuel_service_providers, name='fuel_service'),
    path('services/towing/', towing_service, name='towing_service'),
    path('services/mechanic/', mechanic_service, name='mechanic_service'),
    path('services/battery/', battery_service, name='battery_service'),
    path('services/tire/', tire_service, name='tire_service'),
    path('services/lockout/', lockout_service, name='lockout_service'),
    
    # Provider URLs
    path('provider/register/', provider_register, name='provider_register'),
    path('provider/dashboard/', provider_dashboard, name='provider_dashboard'),
    
    # Service Request URLs
    path('service-request/<int:provider_id>/<int:category_id>/', create_service_request, name='create_service_request'),
    path('service-request/update/<int:request_id>/', update_service_request, name='update_service_request'),
    
    # Admin Dashboard
    path('admins/dashboard/', admin_dashboard, name='admin_dashboard'),
    
    # Include auth views for password reset
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
