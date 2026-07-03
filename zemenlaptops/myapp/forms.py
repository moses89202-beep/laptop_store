from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Customer

# --- SIGNUP FORM ---
class CustomerSignupForm(UserCreationForm):
    full_name = forms.CharField(max_length=255, required=True, label="Full Name")
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def clean_email(self):
        """Enforces that the email cannot already exist during signup."""
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email address already exists.")
        return email

    def save(self, commit=True):
        # 1. Save the core User account first
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        # Split the full name into first and last name for Django's built-in User model fields if desired
        names = self.cleaned_data['full_name'].strip().split(' ', 1)
        user.first_name = names[0]
        user.last_name = names[1] if len(names) > 1 else ""
        
        if commit:
            user.save()
            # 2. Create the linked Customer profile instantly
            Customer.objects.create(
                user=user,
                full_name=self.cleaned_data.get('full_name'),  # Saved to customer profile
                phone_number=self.cleaned_data.get('phone_number'),
                address=self.cleaned_data.get('address')
            )
        return user


# --- LOGIN FORM ---
class CustomerLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})


# --- PROFILE UPDATE FORM ---
class CustomerProfileForm(forms.ModelForm):
    full_name = forms.CharField(max_length=255, required=True, label="Full Name")
    email = forms.EmailField(required=True)

    class Meta:
        model = Customer
        fields = ['phone_number', 'address']

    def __init__(self, *args, **kwargs):
        # Populating fields with current user data on initialization
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['email'].initial = self.user.email
            # Fetch full name from the instance if it exists
            if self.instance and hasattr(self.instance, 'full_name'):
                self.fields['full_name'].initial = self.instance.full_name

    def clean_email(self):
        """Ensures the updated email isn't taken by *someone else*."""
        email = self.cleaned_data.get('email').lower()
        if self.user:
            # Exclude the current user from the check so they can save their own email
            if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
                raise ValidationError("A user with this email address already exists.")
        return email

    def save(self, commit=True):
        # 1. Update user email and name fields on the core User model
        if self.user:
            self.user.email = self.cleaned_data['email']
            names = self.cleaned_data['full_name'].strip().split(' ', 1)
            self.user.first_name = names[0]
            self.user.last_name = names[1] if len(names) > 1 else ""
            self.user.save()
        
        # 2. Update profile instance fields
        profile = super().save(commit=False)
        profile.full_name = self.cleaned_data['full_name']
        
        if commit:
            profile.save()
        return profile