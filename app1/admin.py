from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from .models import ServiceCategory, ServiceProvider, Service, Booking, Review, SystemSetting
from django.urls import reverse
from django.utils.safestring import mark_safe

# Unregister default Group model
admin.site.unregister(Group)

class ServiceProviderInline(admin.StackedInline):
    model = ServiceProvider
    can_delete = False
    verbose_name_plural = 'Service Provider Details'
    fk_name = 'user'
    extra = 0
    fields = ('company_name', 'phone_number', 'address', 'is_approved', 'is_active')

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_service_provider', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    inlines = (ServiceProviderInline, )

    def is_service_provider(self, obj):
        return hasattr(obj, 'service_provider')
    is_service_provider.boolean = True
    is_service_provider.short_description = 'Is Provider'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'description': ('name',)}
    ordering = ('name',)

@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user_email', 'phone_number', 'is_approved', 'is_active', 'created_at')
    list_filter = ('is_approved', 'is_active', 'created_at')
    search_fields = ('company_name', 'user__email', 'user__first_name', 'user__last_name')
    list_editable = ('is_approved', 'is_active')
    raw_id_fields = ('user',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider_name', 'category', 'price', 'is_available', 'created_at')
    list_filter = ('category', 'is_available', 'created_at')
    search_fields = ('title', 'description', 'provider__company_name')
    list_editable = ('is_available', 'price')
    raw_id_fields = ('provider', 'category')
    
    def provider_name(self, obj):
        return obj.provider.company_name
    provider_name.short_description = 'Provider'
    provider_name.admin_order_field = 'provider__company_name'

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'service_title', 'customer_name', 'booking_date', 'status', 'created_at')
    list_filter = ('status', 'booking_date', 'created_at')
    search_fields = ('service__title', 'customer__username', 'customer__email')
    list_editable = ('status',)
    date_hierarchy = 'booking_date'
    
    def service_title(self, obj):
        return obj.service.title
    service_title.short_description = 'Service'
    service_title.admin_order_field = 'service__title'
    
    def customer_name(self, obj):
        return f"{obj.customer.get_full_name() or obj.customer.username}"
    customer_name.short_description = 'Customer'
    customer_name.admin_order_field = 'customer__first_name'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('rating_stars', 'booking_info', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('booking__service__title', 'booking__customer__username', 'comment')
    
    def rating_stars(self, obj):
        return '★' * obj.rating + '☆' * (5 - obj.rating)
    rating_stars.short_description = 'Rating'
    
    def booking_info(self, obj):
        return f"{obj.booking.service.title} - {obj.booking.customer.username}"
    booking_info.short_description = 'Booking'

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value_preview', 'is_active', 'updated_at')
    list_editable = ('is_active',)
    search_fields = ('key', 'description')
    
    def value_preview(self, obj):
        return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
    value_preview.short_description = 'Value'

# Custom admin site header and title
admin.site.site_header = 'Roadside Assistance Admin'
admin.site.site_title = 'Roadside Assistance Administration'
admin.site.index_title = 'Dashboard Overview'
