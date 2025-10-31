from django.contrib import admin
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.admin import AdminSite


class CustomAdminSite(AdminSite):
    site_header = 'RoadMate Administration'
    site_title = 'RoadMate Admin Portal'
    index_title = 'Welcome to RoadMate Admin'
    
    def admin_view(self, view, cacheable=False):
        view = super().admin_view(view, cacheable)
        
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
                # If user is admin and trying to access the default admin, redirect to custom dashboard
                if request.path == reverse('admin:index'):
                    return redirect('admin_dashboard')
            return view(request, *args, **kwargs)
        
        return wrapper

# Create an instance of our custom admin site
custom_admin_site = CustomAdminSite(name='custom_admin')

# Register your models here if needed
# custom_admin_site.register(YourModel)
