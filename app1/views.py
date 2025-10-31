from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy
from django.db.models import Count, Sum, Q
from django.utils import timezone
from .models import Booking, Service, ServiceProvider, Review, ServiceCategory
from .forms import ProviderRegistrationForm, ServiceProviderLoginForm

# Check if user is admin
def admin_required(user):
    return user.is_authenticated and user.is_staff

def home(request):
    # Ensure admin user exists
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@roadmate.com', 'roadmate')
    
    # Explicitly pass the user object to the template context
    context = {
        'user': request.user,
    }
    return render(request, 'home.html', context)

def custom_login(request):
    # If user is already authenticated, redirect to appropriate page
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        elif hasattr(request.user, 'service_provider'):
            return redirect('provider_dashboard')
        return redirect('home')
    
    # Get the next URL from the query parameters or set a default
    next_url = request.GET.get('next', '')
    login_form = None
    
    if request.method == 'POST':
        # Check if this is a provider login
        if 'provider_login' in request.POST:
            login_form = ServiceProviderLoginForm(request.POST)
            if login_form.is_valid():
                user = login_form.user
                login(request, user)
                messages.success(request, 'Successfully logged in as service provider.')
                return redirect('provider_dashboard')
            else:
                # Display form errors as messages
                for error in login_form.non_field_errors():
                    messages.error(request, error)
        else:
            # Regular user login
            username = request.POST.get('username')
            password = request.POST.get('password')
            next_url = request.POST.get('next', next_url)
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # Check if user is staff/superuser
                if user.is_staff or user.is_superuser:
                    user.is_staff = True
                    user.save()
                    return redirect('/admins/dashboard/')
                # Check if user is a verified provider
                elif hasattr(user, 'service_provider') and user.service_provider.is_approved:
                    return redirect('provider_dashboard')
                # Regular user
                elif next_url and next_url != 'None':
                    return redirect(next_url)
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
    
    # For GET requests or failed login
    # Check if we should show the provider tab by default
    show_provider_tab = request.GET.get('type') == 'provider' or 'provider_login' in request.POST
    
    context = {
        'next': next_url if next_url and next_url != 'None' else '',
        'login_form': login_form or ServiceProviderLoginForm(),
        'show_provider_tab': show_provider_tab
    }
    return render(request, 'login.html', context)

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            messages.success(request, f'Account created for {username}!')
            return redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

def custom_logout(request):
    """Handle user logout."""
    # Log the user out
    logout(request)
    
    # Add a success message
    messages.success(request, 'You have been successfully logged out.')
    
    # Redirect to the home page
    return redirect('home')

def service_detail(request, service_slug):
    """Dynamic view for service categories."""
    # Map slugs to service category names
    slug_to_name = {
        'fuel-delivery': 'Fuel Delivery',
        'towing': 'Towing Service',
        'mechanic': 'On-Site Mechanic',
        'battery': 'Battery Jump Start',
        'tire': 'Tire Change',
        'lockout': 'Lockout Service',
    }
    
    service_name = slug_to_name.get(service_slug)
    
    if not service_name:
        messages.error(request, 'Service not found.')
        return redirect('home')
    
    try:
        # Get the service category from database
        category = ServiceCategory.objects.get(name=service_name, is_active=True)
        
        # Get providers offering this service
        providers = ServiceProvider.objects.filter(
            service_categories=category,
            is_approved=True,
            is_active=True
        ).select_related('user')
        
        context = {
            'category': category,
            'service_name': category.name,
            'service_icon': category.icon,
            'service_description': category.description,
            'providers': providers,
            'providers_count': providers.count(),
        }
        
        return render(request, 'service_template.html', context)
        
    except ServiceCategory.DoesNotExist:
        messages.error(request, 'Service category not found.')
        return redirect('home')

# Keep these for backward compatibility, but redirect to the dynamic view
def fuel_service_providers(request):
    return service_detail(request, 'fuel-delivery')

def towing_service(request):
    return service_detail(request, 'towing')

def mechanic_service(request):
    return service_detail(request, 'mechanic')

def battery_service(request):
    return service_detail(request, 'battery')

def tire_service(request):
    return service_detail(request, 'tire')

def lockout_service(request):
    return service_detail(request, 'lockout')

@login_required
def create_service_request(request, provider_id, category_id):
    """Create a service request from customer to provider."""
    if request.method == 'POST':
        try:
            provider = ServiceProvider.objects.get(id=provider_id, is_approved=True, is_active=True)
            category = ServiceCategory.objects.get(id=category_id)
            
            # Create service request
            from .models import ServiceRequest
            service_request = ServiceRequest.objects.create(
                provider=provider,
                customer=request.user,
                service_category=category,
                customer_name=request.POST.get('customer_name', request.user.get_full_name() or request.user.username),
                customer_phone=request.POST.get('customer_phone', ''),
                customer_location=request.POST.get('customer_location', ''),
                description=request.POST.get('description', ''),
                status='pending'
            )
            
            messages.success(
                request, 
                f'Service request sent to {provider.company_name}! They will contact you shortly at {service_request.customer_phone}.'
            )
            
            # Redirect back to the referring page or home
            referer = request.META.get('HTTP_REFERER', '/')
            return redirect(referer if referer else 'home')
            
        except (ServiceProvider.DoesNotExist, ServiceCategory.DoesNotExist):
            messages.error(request, 'Provider or service not found.')
            return redirect('home')
    
    return redirect('home')

@login_required
def update_service_request(request, request_id):
    """Update service request status (accept/reject)."""
    if request.method == 'POST':
        try:
            from .models import ServiceRequest
            service_request = ServiceRequest.objects.get(id=request_id)
            
            # Check if the logged-in user is the provider
            if not hasattr(request.user, 'service_provider') or service_request.provider != request.user.service_provider:
                messages.error(request, 'You do not have permission to update this request.')
                return redirect('provider_dashboard')
            
            action = request.POST.get('action')
            if action == 'accept':
                service_request.status = 'accepted'
                service_request.save()
                messages.success(request, f'Service request from {service_request.customer_name} has been accepted!')
            elif action == 'reject':
                service_request.status = 'cancelled'
                service_request.save()
                messages.info(request, f'Service request from {service_request.customer_name} has been rejected.')
            elif action == 'complete':
                service_request.status = 'completed'
                service_request.save()
                messages.success(request, f'Service request marked as completed!')
            
        except ServiceRequest.DoesNotExist:
            messages.error(request, 'Service request not found.')
    
    return redirect('provider_dashboard')

@login_required
def user_profile(request):
    """User profile page."""
    if request.method == 'POST':
        # Update user information
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', user.email)
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('user_profile')
    
    context = {
        'user': request.user,
    }
    return render(request, 'user_profile.html', context)

@login_required
def my_bookings(request):
    """User's service request bookings."""
    from .models import ServiceRequest
    
    # Get all service requests made by the user
    bookings = ServiceRequest.objects.filter(
        customer=request.user
    ).select_related('provider', 'service_category').order_by('-created_at')
    
    # Categorize bookings by status
    pending_bookings = bookings.filter(status='pending')
    active_bookings = bookings.filter(status__in=['accepted', 'in_progress'])
    completed_bookings = bookings.filter(status='completed')
    cancelled_bookings = bookings.filter(status='cancelled')
    
    context = {
        'bookings': bookings,
        'pending_bookings': pending_bookings,
        'active_bookings': active_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'total_bookings': bookings.count(),
    }
    return render(request, 'my_bookings.html', context)

@login_required
@user_passes_test(admin_required, login_url='login')
def admin_dashboard(request):
    """Custom admin dashboard view."""
    # Ensure the user is staff
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
        
    from django.contrib.auth import get_user_model
    from django.db.models import Count, Sum
    
    User = get_user_model()

    # Ensure admin user exists
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@roadmate.com', 'roadmate')

    # Handle provider approval
    if request.method == 'POST' and 'approve_provider' in request.POST:
        provider_id = request.POST.get('provider_id')
        try:
            provider = ServiceProvider.objects.get(id=provider_id)
            provider.is_approved = True
            provider.save()
            
            # Activate the user account
            provider.user.is_active = True
            provider.user.save()
            
            messages.success(request, f'Provider "{provider.company_name}" has been approved!')
        except ServiceProvider.DoesNotExist:
            messages.error(request, 'Provider not found.')
    
    # Handle provider rejection
    if request.method == 'POST' and 'reject_provider' in request.POST:
        provider_id = request.POST.get('provider_id')
        try:
            provider = ServiceProvider.objects.get(id=provider_id)
            # Delete the provider and associated user
            user = provider.user
            provider.delete()
            user.delete()
            
            messages.success(request, f'Provider request has been rejected and removed.')
        except ServiceProvider.DoesNotExist:
            messages.error(request, 'Provider not found.')

    try:
        from .models import ServiceRequest
        
        # Get pending providers
        pending_providers = ServiceProvider.objects.filter(is_approved=False).select_related('user')
        
        # Get all providers
        all_providers = ServiceProvider.objects.filter(is_approved=True).select_related('user').prefetch_related('service_categories')
        
        # Get all service requests
        all_requests = ServiceRequest.objects.all().select_related('customer', 'provider', 'service_category')
        recent_requests = all_requests.order_by('-created_at')[:10]
        
        # Get statistics
        stats = {
            'total_users': User.objects.filter(is_staff=False).count(),
            'active_providers': ServiceProvider.objects.filter(is_active=True, is_approved=True).count(),
            'pending_providers': pending_providers.count(),
            'total_providers': ServiceProvider.objects.count(),
            'total_requests': all_requests.count(),
            'pending_requests': all_requests.filter(status='pending').count(),
            'active_requests': all_requests.filter(status__in=['accepted', 'in_progress']).count(),
            'completed_requests': all_requests.filter(status='completed').count(),
        }
    except Exception as e:
        # If there's an error (e.g., models not migrated yet), use default values
        pending_providers = []
        all_providers = []
        recent_requests = []
        stats = {
            'total_users': 0,
            'active_providers': 0,
            'pending_providers': 0,
            'total_providers': 0,
            'total_requests': 0,
            'pending_requests': 0,
            'active_requests': 0,
            'completed_requests': 0,
        }
    
    context = {
        'title': 'Admin Dashboard',
        'stats': stats,
        'pending_providers': pending_providers,
        'all_providers': all_providers,
        'recent_requests': recent_requests,
        'current_date': timezone.now().date(),
    }
    
    return render(request, 'admin_dashboard_simple.html', context)

def provider_register(request):
    # Check if user is already logged in
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = ProviderRegistrationForm(request.POST)
        if form.is_valid():
            try:
                provider = form.save()
                messages.success(
                    request,
                    'Your provider account has been created successfully! ' \
                    'Please wait for admin approval before logging in.'
                )
                # Redirect to login page with provider tab selected
                from django.urls import reverse
                login_url = f"{reverse('login')}?type=provider"
                return redirect(login_url)
            except Exception as e:
                messages.error(
                    request,
                    f'An error occurred while creating your account: {str(e)}'
                )
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = ProviderRegistrationForm()
    
    return render(request, 'provider_register.html', {'form': form})

@login_required
def provider_dashboard(request):
    """View for the service provider dashboard."""
    # Check if user is a service provider
    if not hasattr(request.user, 'service_provider'):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('home')
    
    # Get the provider instance
    provider = request.user.service_provider
    
    # Only show dashboard if provider is approved
    if not provider.is_approved:
        messages.warning(
            request,
            'Your account is pending approval from the administrator. '
            'You will be able to access the dashboard once approved.'
        )
        return redirect('home')
    
    # Get provider's services
    try:
        services = Service.objects.filter(provider=provider)
        total_services = services.count()
    except:
        services = []
        total_services = 0
    
    # Get recent bookings
    try:
        recent_bookings = Booking.objects.filter(
            service__provider=provider
        ).select_related('service').order_by('-created_at')[:5]
        
        active_bookings = Booking.objects.filter(
            service__provider=provider,
            status__in=['pending', 'confirmed', 'in_progress']
        ).count()
    except:
        recent_bookings = []
        active_bookings = 0
    
    # Get service categories
    service_categories = provider.service_categories.all()
    
    # Get service requests
    from .models import ServiceRequest
    
    # Count pending requests first (before slicing)
    pending_requests = ServiceRequest.objects.filter(
        provider=provider,
        status='pending'
    ).count()
    
    # Get recent service requests (limited to 10)
    service_requests = ServiceRequest.objects.filter(
        provider=provider
    ).select_related('customer', 'service_category').order_by('-created_at')[:10]
    
    # Calculate statistics
    stats = {
        'total_services': total_services,
        'active_bookings': active_bookings,
        'service_categories': service_categories.count(),
        'company_name': provider.company_name,
        'pending_requests': pending_requests,
    }
    
    context = {
        'provider': provider,
        'services': services,
        'recent_bookings': recent_bookings,
        'stats': stats,
        'service_categories': service_categories,
        'service_requests': service_requests,
    }
    
    return render(request, 'provider_dashboard.html', context)