from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model, authenticate
from .models import ServiceProvider, ServiceCategory

User = get_user_model()

class ProviderRegistrationForm(forms.ModelForm):
    """Form for service provider registration."""
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    service_categories = forms.ModelMultipleChoiceField(
        queryset=ServiceCategory.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Services You Provide"
    )
    
    class Meta:
        model = ServiceProvider
        fields = ['company_name', 'phone_number', 'address', 'service_categories']
        
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
        
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords don't match")
            
        return cleaned_data
        
    def save(self, commit=True):
        # Create the user first
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            is_active=False  # Inactive until admin approves
        )
        
        # Create the service provider
        provider = super().save(commit=False)
        provider.user = user
        provider.is_approved = False  # Not approved by default
        
        if commit:
            provider.save()
            # Save the ManyToMany relationship
            self.save_m2m()
            
        return provider

class ServiceProviderLoginForm(forms.Form):
    """Form for service provider login."""
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError("Invalid username or password.")
            
            # Check if user is a service provider
            if not hasattr(user, 'service_provider'):
                raise forms.ValidationError("This account is not registered as a service provider.")
            
            # Check if user account is active
            if not user.is_active:
                raise forms.ValidationError("Your account is inactive. Please contact the administrator.")
                
            # Check if provider is approved
            if not user.service_provider.is_approved:
                raise forms.ValidationError("Your account is pending approval from the administrator.")
                
            self.user = user
            
        return cleaned_data
